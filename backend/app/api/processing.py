import os
import shutil
import uuid
import logging
from pathlib import Path
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, status
from sqlalchemy.orm import Session

from app.database import get_db, SessionLocal
from app.config import settings
from app.models.meeting import Meeting, TranscriptSegment, Decision, ActionItem
from app.schemas.meeting import MeetingDetailRead, ProcessingStatusRead
from app.services.audio_service import audio_service
from app.services.transcription_service import transcription_service
from app.services.extraction_service import extraction_service

logger = logging.getLogger("echonote.processing")

router = APIRouter(prefix="/api", tags=["processing"])

# Global in-memory progress tracker: meeting_id -> dict(status, progress, current_step, error_message)
processing_progress: Dict[str, Dict[str, Any]] = {}

def update_status(meeting_id: str, status_str: str, progress: int, current_step: str, error: str = None):
    processing_progress[meeting_id] = {
        "meeting_id": meeting_id,
        "status": status_str,
        "progress": progress,
        "current_step": current_step,
        "error_message": error
    }

def run_processing_pipeline(meeting_id: str):
    """
    Background worker that runs the full audio -> transcription -> extraction -> validation pipeline.
    """
    db = SessionLocal()
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        db.close()
        return

    try:
        meeting.status = "processing"
        db.commit()
        update_status(meeting_id, "processing", 10, "Converting audio format to standard WAV...")

        # 1. Convert to 16kHz mono WAV
        processed_filename = f"{meeting.id}_normalized.wav"
        processed_path = str(Path(settings.PROCESSED_DIR) / processed_filename)
        
        audio_service.convert_to_standard_wav(
            input_path=meeting.file_path,
            output_path=processed_path
        )
        meeting.processed_file_path = processed_path

        # Duration should reflect the original file (compressed formats have different
        # byte sizes than their PCM equivalents).  Probe the original upload, not the
        # normalized PCM copy which always reads as a shorter duration at 16kHz mono.
        try:
            original_info = audio_service.get_audio_info(meeting.file_path)
            original_duration = float(original_info.get("duration", 0.0))
        except Exception:
            original_duration = 0.0

        if original_duration > 0:
            meeting.duration = original_duration
        else:
            # Fallback: use normalized file duration (accurate for PCM originals)
            audio_info = audio_service.get_audio_info(processed_path)
            if audio_info.get("duration"):
                meeting.duration = float(audio_info["duration"])

        logger.info(f"Meeting {meeting_id}: original duration = {meeting.duration:.2f}s")
        db.commit()

        # 2. Chunk-based Transcription with Whisper & Speaker labeling
        update_status(meeting_id, "processing", 30, "Transcribing speech and assigning speakers...")
        
        def on_transcribe_progress(pct, step_desc):
            update_status(meeting_id, "processing", pct, step_desc)

        segments_data = transcription_service.process_full_audio(
            audio_path=processed_path,
            total_duration_sec=meeting.duration,
            progress_callback=on_transcribe_progress
        )

        # Clear any prior segments if re-processing
        db.query(TranscriptSegment).filter(TranscriptSegment.meeting_id == meeting.id).delete()
        
        # Save transcript segments
        for seg in segments_data:
            db_segment = TranscriptSegment(
                id=str(uuid.uuid4()),
                meeting_id=meeting.id,
                start_time=seg["start_time"],
                end_time=seg["end_time"],
                speaker=seg["speaker"],
                text=seg["text"]
            )
            db.add(db_segment)
        db.commit()

        # 3. LLM Structured Extraction & Evidence Validation
        update_status(meeting_id, "processing", 80, "Extracting structured insights and validating evidence...")

        from app.services.llm_service import MockLLMProvider, get_llm_provider as _get_llm
        _active_provider = _get_llm()
        if isinstance(_active_provider, MockLLMProvider):
            logger.warning(
                "MOCK LLM PROVIDER is active for meeting %s. "
                "Extraction uses keyword heuristics — not a real AI model. "
                "Set LLM_PROVIDER=openai or LLM_PROVIDER=gemini with LLM_API_KEY "
                "in backend/.env for real AI-powered meeting intelligence.",
                meeting_id
            )
        
        extraction, val_decisions, val_actions = extraction_service.extract_and_validate(segments_data)

        # Update meeting summary, points, questions, topics
        meeting.summary = extraction.summary
        meeting.key_points = extraction.key_points
        meeting.unresolved_questions = extraction.unresolved_questions
        meeting.important_topics = extraction.important_topics

        # Clear prior decisions & action items
        db.query(Decision).filter(Decision.meeting_id == meeting.id).delete()
        db.query(ActionItem).filter(ActionItem.meeting_id == meeting.id).delete()

        # Save validated decisions
        for d in val_decisions:
            db_dec = Decision(
                id=str(uuid.uuid4()),
                meeting_id=meeting.id,
                description=d.get("description", ""),
                speaker=d.get("speaker"),
                timestamp=d.get("timestamp"),
                evidence=d.get("evidence"),
                confidence=d.get("confidence", 0.0),
                validation_status=d.get("validation_status", "unverified")
            )
            db.add(db_dec)

        # Save validated action items
        for a in val_actions:
            db_act = ActionItem(
                id=str(uuid.uuid4()),
                meeting_id=meeting.id,
                task=a.get("task", ""),
                owner=a.get("owner", "Not specified"),
                deadline=a.get("deadline", "Not specified"),
                timestamp=a.get("timestamp"),
                evidence=a.get("evidence"),
                status=a.get("status", "pending"),
                confidence=a.get("confidence", 0.0),
                validation_status=a.get("validation_status", "unverified")
            )
            db.add(db_act)

        meeting.status = "completed"
        meeting.error_message = None
        db.commit()

        update_status(meeting_id, "completed", 100, "Processing complete!")

    except Exception as e:
        logger.exception(f"Pipeline error for meeting {meeting_id}: {e}")
        meeting.status = "failed"
        meeting.error_message = str(e)
        db.commit()
        update_status(meeting_id, "failed", 0, "Processing failed", error=str(e))
    finally:
        db.close()


@router.post("/upload")
async def upload_recording(
    file: UploadFile = File(...),
    title: str = Form(None),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    auto_process: bool = Form(True),
    db: Session = Depends(get_db)
):
    """
    Step 1 & 2: Receive and validate uploaded recording.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected")

    # Check extension
    is_valid, err = audio_service.validate_file(file.filename, 0)
    if not is_valid:
        raise HTTPException(status_code=400, detail=err)

    meeting_id = str(uuid.uuid4())
    ext = Path(file.filename).suffix.lower()
    saved_filename = f"{meeting_id}{ext}"
    saved_path = str(Path(settings.UPLOAD_DIR) / saved_filename)

    # Stream file to disk while validating size
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    total_bytes = 0
    try:
        with open(saved_path, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):
                total_bytes += len(chunk)
                if total_bytes > max_bytes:
                    buffer.close()
                    os.remove(saved_path)
                    raise HTTPException(
                        status_code=400,
                        detail=f"File exceeds maximum upload size of {settings.MAX_UPLOAD_SIZE_MB}MB"
                    )
                buffer.write(chunk)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save upload: {e}")

    # Inspect duration & audio readability
    try:
        info = audio_service.get_audio_info(saved_path)
        duration = float(info.get("duration", 0.0))
    except Exception as e:
        logger.warning(f"Could not probe audio: {e}")
        duration = 0.0

    meeting_title = title.strip() if (title and title.strip()) else Path(file.filename).stem.replace("_", " ").title()

    new_meeting = Meeting(
        id=meeting_id,
        title=meeting_title,
        original_filename=file.filename,
        duration=duration,
        file_path=saved_path,
        status="uploaded"
    )
    db.add(new_meeting)
    db.commit()
    db.refresh(new_meeting)

    update_status(meeting_id, "uploaded", 0, "Uploaded successfully")

    if auto_process:
        background_tasks.add_task(run_processing_pipeline, meeting_id)

    return {
        "id": new_meeting.id,
        "title": new_meeting.title,
        "original_filename": new_meeting.original_filename,
        "duration": new_meeting.duration,
        "status": new_meeting.status,
        "message": "File uploaded and scheduled for processing." if auto_process else "File uploaded successfully."
    }


@router.post("/process/{meeting_id}")
def trigger_processing(
    meeting_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    if meeting.status == "processing":
        return {"message": "Meeting is already being processed.", "meeting_id": meeting_id}

    background_tasks.add_task(run_processing_pipeline, meeting_id)
    return {"message": "Processing started.", "meeting_id": meeting_id}


@router.get("/status/{meeting_id}", response_model=ProcessingStatusRead)
def get_processing_status(meeting_id: str, db: Session = Depends(get_db)):
    # Check in-memory first
    if meeting_id in processing_progress:
        data = processing_progress[meeting_id]
        return ProcessingStatusRead(
            meeting_id=meeting_id,
            status=data["status"],
            progress=data["progress"],
            current_step=data["current_step"],
            error_message=data.get("error_message")
        )

    # Fallback to database
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    progress = 100 if meeting.status == "completed" else (0 if meeting.status in ["uploaded", "failed"] else 50)
    return ProcessingStatusRead(
        meeting_id=meeting.id,
        status=meeting.status,
        progress=progress,
        current_step=meeting.status.capitalize(),
        error_message=meeting.error_message
    )
