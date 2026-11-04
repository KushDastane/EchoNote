from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.meeting import Meeting, TranscriptSegment, Decision, ActionItem
from app.schemas.meeting import SearchResultItem, SearchResponse

class SearchService:
    def search(self, db: Session, query_str: str) -> SearchResponse:
        """
        Multi-field search across titles, transcripts, decisions, and action items.
        """
        clean_q = query_str.strip()
        if not clean_q:
            return SearchResponse(query="", total_matches=0, results=[])

        like_pattern = f"%{clean_q}%"
        results: List[SearchResultItem] = []

        # 1. Search Meeting Titles
        meetings = db.query(Meeting).filter(Meeting.title.ilike(like_pattern)).all()
        for m in meetings:
            results.append(SearchResultItem(
                meeting_id=m.id,
                meeting_title=m.title,
                type="title",
                text=m.title,
                timestamp=0.0
            ))

        # 2. Search Decisions
        decisions = (
            db.query(Decision, Meeting)
            .join(Meeting, Decision.meeting_id == Meeting.id)
            .filter(or_(Decision.description.ilike(like_pattern), Decision.evidence.ilike(like_pattern)))
            .all()
        )
        for dec, m in decisions:
            results.append(SearchResultItem(
                meeting_id=m.id,
                meeting_title=m.title,
                type="decision",
                text=dec.description,
                timestamp=dec.timestamp,
                speaker=dec.speaker,
                evidence=dec.evidence,
                status=dec.validation_status
            ))

        # 3. Search Action Items
        action_items = (
            db.query(ActionItem, Meeting)
            .join(Meeting, ActionItem.meeting_id == Meeting.id)
            .filter(or_(ActionItem.task.ilike(like_pattern), ActionItem.evidence.ilike(like_pattern)))
            .all()
        )
        for act, m in action_items:
            results.append(SearchResultItem(
                meeting_id=m.id,
                meeting_title=m.title,
                type="action_item",
                text=act.task,
                timestamp=act.timestamp,
                evidence=act.evidence,
                status=act.status
            ))

        # 4. Search Transcript Segments
        segments = (
            db.query(TranscriptSegment, Meeting)
            .join(Meeting, TranscriptSegment.meeting_id == Meeting.id)
            .filter(TranscriptSegment.text.ilike(like_pattern))
            .limit(50)
            .all()
        )
        for seg, m in segments:
            results.append(SearchResultItem(
                meeting_id=m.id,
                meeting_title=m.title,
                type="transcript",
                text=seg.text,
                timestamp=seg.start_time,
                speaker=seg.speaker
            ))

        return SearchResponse(
            query=clean_q,
            total_matches=len(results),
            results=results
        )

search_service = SearchService()
