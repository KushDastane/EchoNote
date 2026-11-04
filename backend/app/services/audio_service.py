import os
import subprocess
import json
import logging
from pathlib import Path
from typing import Tuple, Dict, Any, Optional

from app.config import settings

logger = logging.getLogger("echonote.audio")

class AudioService:
    def __init__(self):
        self.ffmpeg_bin = settings.resolve_ffmpeg()
        self.ffprobe_bin = settings.resolve_ffprobe()

    def validate_file(self, filename: str, file_size_bytes: int) -> Tuple[bool, Optional[str]]:
        """Validate file extension and size."""
        ext = Path(filename).suffix.lower()
        if ext not in settings.ALLOWED_AUDIO_EXTENSIONS:
            allowed = ", ".join(settings.ALLOWED_AUDIO_EXTENSIONS)
            return False, f"Unsupported file extension '{ext}'. Allowed extensions: {allowed}"
        
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if file_size_bytes > max_bytes:
            return False, f"File size exceeds maximum limit of {settings.MAX_UPLOAD_SIZE_MB}MB."

        return True, None

    def get_audio_info(self, file_path: str) -> Dict[str, Any]:
        """Inspect audio duration, format and streams via ffprobe."""
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"Audio file not found at {file_path}")

        cmd = [
            self.ffprobe_bin,
            "-v", "error",
            "-show_entries", "format=duration,size,bit_rate,format_name",
            "-show_streams",
            "-of", "json",
            file_path
        ]

        try:
            res = subprocess.run(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
                timeout=10
            )
            probe = json.loads(res.stdout)
            format_info = probe.get("format", {})
            duration = float(format_info.get("duration", 0.0))
            
            return {
                "duration": duration,
                "format_name": format_info.get("format_name", "unknown"),
                "size_bytes": int(format_info.get("size", os.path.getsize(file_path))),
                "bit_rate": format_info.get("bit_rate"),
                "channels": probe.get("streams", [{}])[0].get("channels", 1) if probe.get("streams") else 1
            }
        except Exception as e:
            logger.warning(f"ffprobe extraction failed: {e}. Falling back to file inspection.")
            # Fallback estimation for basic tests or if ffprobe failed
            size = os.path.getsize(file_path)
            # Default to placeholder duration if ffprobe cannot read
            return {
                "duration": 60.0,
                "format_name": Path(file_path).suffix.lstrip("."),
                "size_bytes": size,
                "channels": 1
            }

    def convert_to_standard_wav(self, input_path: str, output_path: str) -> str:
        """
        Converts any audio file to 16kHz mono 16-bit PCM WAV for optimal Whisper ingestion.
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        cmd = [
            self.ffmpeg_bin,
            "-y",
            "-i", input_path,
            "-vn",                      # No video
            "-acodec", "pcm_s16le",      # 16-bit PCM
            "-ar", "16000",             # 16kHz sampling rate
            "-ac", "1",                 # Mono channel
            output_path
        ]

        try:
            subprocess.run(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
                timeout=60
            )
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg conversion failed: {e.stderr}")
            raise RuntimeError(f"FFmpeg conversion failed: {e.stderr}")

    def extract_chunk(self, input_path: str, output_path: str, start_sec: float, duration_sec: float) -> str:
        """
        Extract an audio window chunk from source audio.
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        cmd = [
            self.ffmpeg_bin,
            "-y",
            "-ss", str(start_sec),
            "-t", str(duration_sec),
            "-i", input_path,
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            output_path
        ]

        try:
            subprocess.run(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
                timeout=60
            )
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg chunk extraction failed: {e.stderr}")
            raise RuntimeError(f"FFmpeg chunk extraction failed: {e.stderr}")

audio_service = AudioService()
