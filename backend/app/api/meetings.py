import os
import re
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.meeting import Meeting, TranscriptSegment, Decision, ActionItem
from app.schemas.meeting import (
    MeetingListItem,
    MeetingDetailRead,
    ActionItemUpdate,
    ActionItemRead,
    DashboardMetrics
)

router = APIRouter(prefix="/api/meetings", tags=["meetings"])

@router.get("", response_model=List[MeetingListItem])
def list_meetings(db: Session = Depends(get_db)):
    meetings = db.query(Meeting).order_by(Meeting.created_at.desc()).all()
    
    result = []
    for m in meetings:
        seg_count = db.query(func.count(TranscriptSegment.id)).filter(TranscriptSegment.meeting_id == m.id).scalar() or 0
        dec_count = db.query(func.count(Decision.id)).filter(Decision.meeting_id == m.id).scalar() or 0
        act_count = db.query(func.count(ActionItem.id)).filter(ActionItem.meeting_id == m.id).scalar() or 0
        pending_act_count = (
            db.query(func.count(ActionItem.id))
            .filter(ActionItem.meeting_id == m.id, ActionItem.status == "pending")
            .scalar() or 0
        )

        result.append(MeetingListItem(
            id=m.id,
            title=m.title,
            original_filename=m.original_filename,
            duration=m.duration,
            status=m.status,
            created_at=m.created_at,
            segment_count=seg_count,
            decision_count=dec_count,
            action_item_count=act_count,
            pending_action_item_count=pending_act_count
        ))
    return result

@router.get("/metrics", response_model=DashboardMetrics)
def get_dashboard_metrics(db: Session = Depends(get_db)):
    total_meetings = db.query(func.count(Meeting.id)).scalar() or 0
    total_duration = db.query(func.sum(Meeting.duration)).scalar() or 0.0
    total_actions = db.query(func.count(ActionItem.id)).scalar() or 0
    pending_actions = (
        db.query(func.count(ActionItem.id))
        .filter(ActionItem.status == "pending")
        .scalar() or 0
    )
    verified_decisions = (
        db.query(func.count(Decision.id))
        .filter(Decision.validation_status == "verified")
        .scalar() or 0
    )

    # Get up to 5 recent meetings
    recent = list_meetings(db)[:5]

    return DashboardMetrics(
        total_meetings=total_meetings,
        total_duration_seconds=float(total_duration),
        total_action_items=total_actions,
        pending_action_items=pending_actions,
        verified_decisions=verified_decisions,
        recent_meetings=recent
    )

@router.get("/{meeting_id}", response_model=MeetingDetailRead)
def get_meeting(meeting_id: str, db: Session = Depends(get_db)):
    m = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not m:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")

    return MeetingDetailRead(
        id=m.id,
        title=m.title,
        original_filename=m.original_filename,
        duration=m.duration,
        status=m.status,
        error_message=m.error_message,
        summary=m.summary,
        key_points=m.key_points,
        unresolved_questions=m.unresolved_questions,
        important_topics=m.important_topics,
        created_at=m.created_at,
        updated_at=m.updated_at,
        segments=m.segments,
        decisions=m.decisions,
        action_items=m.action_items
    )

@router.patch("/{meeting_id}/actions/{action_id}", response_model=ActionItemRead)
def update_action_item(
    meeting_id: str,
    action_id: str,
    update_data: ActionItemUpdate,
    db: Session = Depends(get_db)
):
    action = (
        db.query(ActionItem)
        .filter(ActionItem.id == action_id, ActionItem.meeting_id == meeting_id)
        .first()
    )
    if not action:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Action item not found")

    if update_data.status is not None:
        action.status = update_data.status
    if update_data.owner is not None:
        action.owner = update_data.owner
    if update_data.deadline is not None:
        action.deadline = update_data.deadline

    db.commit()
    db.refresh(action)
    return action

@router.delete("/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meeting(meeting_id: str, db: Session = Depends(get_db)):
    m = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not m:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")

    # Clean up physical files safely
    for path in [m.file_path, m.processed_file_path]:
        if path and os.path.isfile(path):
            try:
                os.remove(path)
            except Exception:
                pass

    db.delete(m)
    db.commit()
    return None

@router.get("/{meeting_id}/audio")
def stream_audio(meeting_id: str, request: Request, db: Session = Depends(get_db)):
    """
    Stream meeting audio with HTTP Range Header support for smooth timeline seeking.
    """
    m = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not m:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")

    # Prefer processed WAV, fall back to uploaded original
    file_path = m.processed_file_path if (m.processed_file_path and os.path.isfile(m.processed_file_path)) else m.file_path

    if not file_path or not os.path.isfile(file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audio file not found on disk")

    file_size = os.path.getsize(file_path)
    range_header = request.headers.get("range")

    ext = os.path.splitext(file_path)[1].lower()
    content_type_map = {
        ".wav": "audio/wav",
        ".mp3": "audio/mpeg",
        ".m4a": "audio/mp4",
        ".aac": "audio/aac",
        ".flac": "audio/flac",
        ".ogg": "audio/ogg",
        ".webm": "audio/webm",
        ".mp4": "audio/mp4"
    }
    content_type = content_type_map.get(ext, "audio/mpeg")

    if not range_header:
        return FileResponse(file_path, media_type=content_type, filename=m.original_filename)

    # Parse range header: "bytes=start-end"
    range_match = re.match(r"bytes=(\d+)-(\d*)", range_header)
    if not range_match:
        return Response(status_code=416, headers={"Content-Range": f"bytes */{file_size}"})

    start = int(range_match.group(1))
    end = int(range_match.group(2)) if range_match.group(2) else file_size - 1

    if start >= file_size or end >= file_size or start > end:
        return Response(status_code=416, headers={"Content-Range": f"bytes */{file_size}"})

    chunk_length = end - start + 1

    def iterfile():
        with open(file_path, "rb") as f:
            f.seek(start)
            bytes_left = chunk_length
            while bytes_left > 0:
                read_size = min(64 * 1024, bytes_left)
                data = f.read(read_size)
                if not data:
                    break
                bytes_left -= len(data)
                yield data

    headers = {
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Accept-Ranges": "bytes",
        "Content-Length": str(chunk_length),
        "Content-Type": content_type,
    }

    return StreamingResponse(iterfile(), status_code=206, headers=headers)
