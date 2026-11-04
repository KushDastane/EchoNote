import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from app.config import settings
from app.utils.audio_chunking import compute_chunk_windows, merge_chunk_segments
from app.services.audio_service import audio_service
from app.services.speaker_service import speaker_service

logger = logging.getLogger("echonote.transcription")

class TranscriptionService:
    def __init__(self):
        self._model = None
        self._whisper_module = None
        self._init_attempted = False

    def _load_model(self):
        if self._model is not None:
            return self._model

        try:
            import whisper
            self._whisper_module = whisper
            logger.info(f"Loading Whisper model '{settings.WHISPER_MODEL}' on {settings.WHISPER_DEVICE}...")
            self._model = whisper.load_model(settings.WHISPER_MODEL, device=settings.WHISPER_DEVICE)
            logger.info("Whisper model loaded successfully.")
            return self._model
        except Exception as e:
            logger.warning(f"Could not load OpenAI Whisper: {e}. Transcription will use fallback processor.")
            self._model = None
            return None

    def transcribe_chunk(self, audio_chunk_path: str) -> List[Dict[str, Any]]:
        """
        Transcribe a single audio chunk and return raw segments with relative start/end.
        """
        model = self._load_model()
        if model is not None:
            try:
                result = model.transcribe(
                    audio_chunk_path,
                    fp16=False,
                    word_timestamps=False,
                    language="en"
                )
                segments = []
                for s in result.get("segments", []):
                    segments.append({
                        "start": float(s["start"]),
                        "end": float(s["end"]),
                        "text": s["text"].strip(),
                        "speaker": "Speaker"
                    })
                return segments
            except Exception as e:
                logger.error(f"Whisper inference error on chunk {audio_chunk_path}: {e}")

        # Whisper is not available — do NOT return fabricated/hardcoded text.
        # Raise a clear error so the pipeline sets the meeting to 'failed' status.
        logger.error(
            "Whisper transcription model is not available. "
            "Cannot transcribe audio without a real model. "
            "Install it with: pip install openai-whisper "
            "(requires torch ~2GB — ensure sufficient disk space)."
        )
        raise RuntimeError(
            "Whisper is not installed. Audio cannot be transcribed. "
            "Run: pip install openai-whisper"
        )

    def process_full_audio(
        self,
        audio_path: str,
        total_duration_sec: float,
        progress_callback: Optional[callable] = None
    ) -> List[Dict[str, Any]]:
        """
        Processes audio using chunk-based pipeline:
        1. Compute chunk windows with overlap.
        2. Extract temporary audio slices.
        3. Transcribe each slice.
        4. Merge segments while maintaining offset timestamps and avoiding duplicates.
        5. Apply speaker identification.
        """
        windows = compute_chunk_windows(
            total_duration_sec=total_duration_sec,
            chunk_length_sec=settings.AUDIO_CHUNK_LENGTH_SEC,
            overlap_sec=settings.AUDIO_CHUNK_OVERLAP_SEC
        )

        chunked_results = []
        temp_dir = Path(settings.PROCESSED_DIR) / "temp_chunks"
        os.makedirs(temp_dir, exist_ok=True)

        for i, win in enumerate(windows):
            chunk_file = str(temp_dir / f"chunk_{os.path.basename(audio_path)}_{i}.wav")
            try:
                # If audio is already small and single window, use original directly
                if len(windows) == 1:
                    chunk_file = audio_path
                else:
                    audio_service.extract_chunk(
                        input_path=audio_path,
                        output_path=chunk_file,
                        start_sec=win["start"],
                        duration_sec=win["duration"]
                    )

                if progress_callback:
                    pct = int(20 + ((i + 1) / len(windows)) * 50)
                    progress_callback(pct, f"Transcribing audio chunk {i + 1} of {len(windows)}...")

                segments = self.transcribe_chunk(chunk_file)
                chunked_results.append((win["offset"], segments))

            finally:
                # Clean up temporary sliced file
                if len(windows) > 1 and os.path.isfile(chunk_file):
                    try:
                        os.remove(chunk_file)
                    except Exception:
                        pass

        # Merge segments across chunk boundaries
        merged_segments = merge_chunk_segments(
            chunked_results,
            overlap_sec=settings.AUDIO_CHUNK_OVERLAP_SEC
        )

        # Apply speaker identification
        labeled_segments = speaker_service.assign_speakers(merged_segments, audio_path)
        return labeled_segments

transcription_service = TranscriptionService()
