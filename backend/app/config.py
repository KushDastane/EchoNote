import os
import shutil
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    HOST: str = "127.0.0.1"
    PORT: int = 8000
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000"

    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'echonote.db'}"

    UPLOAD_DIR: str = str(BASE_DIR / "uploads")
    PROCESSED_DIR: str = str(BASE_DIR / "processed")
    MAX_UPLOAD_SIZE_MB: int = 250

    FFMPEG_PATH: Optional[str] = None
    FFPROBE_PATH: Optional[str] = None

    WHISPER_MODEL: str = "base"
    WHISPER_DEVICE: str = "cpu"

    LLM_PROVIDER: str = "mock"  # "mock", "openai", "gemini"
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_API_KEY: Optional[str] = None

    AUDIO_CHUNK_LENGTH_SEC: int = 600
    AUDIO_CHUNK_OVERLAP_SEC: int = 10

    ALLOWED_AUDIO_EXTENSIONS: List[str] = [
        ".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".webm", ".mp4"
    ]

    def get_cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    def resolve_ffmpeg(self) -> str:
        """Resolve valid ffmpeg binary path."""
        if self.FFMPEG_PATH and os.path.isfile(self.FFMPEG_PATH):
            return self.FFMPEG_PATH
        
        # Check standard PATH
        system_ffmpeg = shutil.which("ffmpeg")
        if system_ffmpeg:
            return system_ffmpeg

        # Check known Windows winget / local installations
        candidates = [
            Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages",
            Path(os.environ.get("ProgramFiles", "")) / "ffmpeg",
            Path("C:/ffmpeg"),
        ]
        for base in candidates:
            if base.exists():
                found = list(base.glob("**/ffmpeg.exe"))
                if found:
                    return str(found[0])
        return "ffmpeg"

    def resolve_ffprobe(self) -> str:
        """Resolve valid ffprobe binary path."""
        if self.FFPROBE_PATH and os.path.isfile(self.FFPROBE_PATH):
            return self.FFPROBE_PATH
        
        system_ffprobe = shutil.which("ffprobe")
        if system_ffprobe:
            return system_ffprobe

        candidates = [
            Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages",
            Path(os.environ.get("ProgramFiles", "")) / "ffmpeg",
            Path("C:/ffmpeg"),
        ]
        for base in candidates:
            if base.exists():
                found = list(base.glob("**/ffprobe.exe"))
                if found:
                    return str(found[0])
        return "ffprobe"

settings = Settings()

# Ensure directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.PROCESSED_DIR, exist_ok=True)
