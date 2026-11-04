import os
os.environ["DISABLE_SQLALCHEMY_CEXT"] = "1"
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.config import settings
from app.database import init_db, get_db
from app.api import meetings, processing, search

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("echonote")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing EchoNote database...")
    init_db()
    logger.info("EchoNote Database initialized.")
    yield
    logger.info("EchoNote application shutdown.")

app = FastAPI(
    title="EchoNote API",
    description="Evidence-backed AI Meeting Intelligence Platform API",
    version="1.0.0",
    lifespan=lifespan
)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(meetings.router)
app.include_router(processing.router)
app.include_router(search.router)

@app.get("/api/health")
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint validating database and engine dependencies."""
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    ffmpeg_bin = settings.resolve_ffmpeg()
    ffprobe_bin = settings.resolve_ffprobe()

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "service": "EchoNote API",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "database": db_status,
        "ffmpeg": {
            "resolved_path": ffmpeg_bin,
            "available": bool(os.path.isfile(ffmpeg_bin) or ffmpeg_bin == "ffmpeg")
        },
        "ffprobe": {
            "resolved_path": ffprobe_bin,
            "available": bool(os.path.isfile(ffprobe_bin) or ffprobe_bin == "ffprobe")
        },
        "ai": {
            "whisper_model": settings.WHISPER_MODEL,
            "whisper_device": settings.WHISPER_DEVICE,
            "llm_provider": settings.LLM_PROVIDER,
            "llm_model": settings.LLM_MODEL
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
