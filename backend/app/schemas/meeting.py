from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, Field, ConfigDict

# ---------------------------------------------------------
# Transcript Segment Schemas
# ---------------------------------------------------------
class TranscriptSegmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    meeting_id: str
    start_time: float
    end_time: float
    speaker: str
    text: str

# ---------------------------------------------------------
# Decision Schemas
# ---------------------------------------------------------
class DecisionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    meeting_id: str
    description: str
    speaker: Optional[str] = None
    timestamp: Optional[float] = None
    evidence: Optional[str] = None
    confidence: float = 0.0
    validation_status: str = "unverified"

# ---------------------------------------------------------
# Action Item Schemas
# ---------------------------------------------------------
class ActionItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    meeting_id: str
    task: str
    owner: Optional[str] = "Not specified"
    deadline: Optional[str] = "Not specified"
    timestamp: Optional[float] = None
    evidence: Optional[str] = None
    status: str = "pending"
    confidence: float = 0.0
    validation_status: str = "unverified"

class ActionItemUpdate(BaseModel):
    status: Optional[str] = None
    owner: Optional[str] = None
    deadline: Optional[str] = None

# ---------------------------------------------------------
# Meeting Schemas
# ---------------------------------------------------------
class MeetingListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    original_filename: str
    duration: float
    status: str
    created_at: datetime
    segment_count: int = 0
    decision_count: int = 0
    action_item_count: int = 0
    pending_action_item_count: int = 0

class MeetingDetailRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    original_filename: str
    duration: float
    status: str
    error_message: Optional[str] = None
    summary: Optional[str] = None
    key_points: List[str] = []
    unresolved_questions: List[str] = []
    important_topics: List[str] = []
    created_at: datetime
    updated_at: datetime
    segments: List[TranscriptSegmentRead] = []
    decisions: List[DecisionRead] = []
    action_items: List[ActionItemRead] = []

# ---------------------------------------------------------
# Processing & Upload Schemas
# ---------------------------------------------------------
class ProcessingStatusRead(BaseModel):
    meeting_id: str
    status: str
    progress: int = 0  # percentage 0-100
    current_step: str = ""
    error_message: Optional[str] = None

# ---------------------------------------------------------
# LLM Extraction Schemas (Section 8 of prompt)
# ---------------------------------------------------------
class LLMDecisionItem(BaseModel):
    description: str
    speaker: Optional[str] = None
    timestamp: Optional[float] = None
    evidence: Optional[str] = ""
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)

class LLMActionItem(BaseModel):
    task: str
    owner: Optional[str] = "Not specified"
    deadline: Optional[str] = "Not specified"
    timestamp: Optional[float] = None
    evidence: Optional[str] = ""
    status: str = "pending"
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)

class LLMExtractionResult(BaseModel):
    summary: str = ""
    key_points: List[str] = []
    decisions: List[LLMDecisionItem] = []
    action_items: List[LLMActionItem] = []
    unresolved_questions: List[str] = []
    important_topics: List[str] = []

# ---------------------------------------------------------
# Dashboard & Search Schemas
# ---------------------------------------------------------
class DashboardMetrics(BaseModel):
    total_meetings: int = 0
    total_duration_seconds: float = 0.0
    total_action_items: int = 0
    pending_action_items: int = 0
    verified_decisions: int = 0
    recent_meetings: List[MeetingListItem] = []

class SearchResultItem(BaseModel):
    meeting_id: str
    meeting_title: str
    type: str  # "title", "transcript", "decision", "action_item"
    text: str
    timestamp: Optional[float] = None
    speaker: Optional[str] = None
    evidence: Optional[str] = None
    status: Optional[str] = None

class SearchResponse(BaseModel):
    query: str
    total_matches: int
    results: List[SearchResultItem]
