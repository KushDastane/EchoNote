from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.search_service import search_service
from app.schemas.meeting import SearchResponse

router = APIRouter(prefix="/api/search", tags=["search"])

@router.get("", response_model=SearchResponse)
def search_meetings(
    q: str = Query("", description="Search term for titles, transcripts, decisions, and action items"),
    db: Session = Depends(get_db)
):
    return search_service.search(db, q)
