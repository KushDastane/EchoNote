import json
import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Float,
    DateTime,
    ForeignKey,
    Text,
    Integer
)
from sqlalchemy.orm import relationship

from app.database import Base

class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    duration = Column(Float, default=0.0)
    file_path = Column(String(500), nullable=False)
    processed_file_path = Column(String(500), nullable=True)
    status = Column(String(50), default="uploaded", nullable=False)  # uploaded, processing, completed, failed
    error_message = Column(Text, nullable=True)
    
    summary = Column(Text, nullable=True)
    key_points_json = Column(Text, nullable=True, default="[]")
    unresolved_questions_json = Column(Text, nullable=True, default="[]")
    important_topics_json = Column(Text, nullable=True, default="[]")
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships with cascade deletion
    segments = relationship("TranscriptSegment", back_populates="meeting", cascade="all, delete-orphan", order_by="TranscriptSegment.start_time")
    decisions = relationship("Decision", back_populates="meeting", cascade="all, delete-orphan")
    action_items = relationship("ActionItem", back_populates="meeting", cascade="all, delete-orphan")

    @property
    def key_points(self):
        if not self.key_points_json:
            return []
        try:
            return json.loads(self.key_points_json)
        except Exception:
            return []

    @key_points.setter
    def key_points(self, val):
        self.key_points_json = json.dumps(val or [])

    @property
    def unresolved_questions(self):
        if not self.unresolved_questions_json:
            return []
        try:
            return json.loads(self.unresolved_questions_json)
        except Exception:
            return []

    @unresolved_questions.setter
    def unresolved_questions(self, val):
        self.unresolved_questions_json = json.dumps(val or [])

    @property
    def important_topics(self):
        if not self.important_topics_json:
            return []
        try:
            return json.loads(self.important_topics_json)
        except Exception:
            return []

    @important_topics.setter
    def important_topics(self, val):
        self.important_topics_json = json.dumps(val or [])


class TranscriptSegment(Base):
    __tablename__ = "transcript_segments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    meeting_id = Column(String(36), ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False, index=True)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    speaker = Column(String(100), default="Speaker", nullable=False)
    text = Column(Text, nullable=False)

    meeting = relationship("Meeting", back_populates="segments")


class Decision(Base):
    __tablename__ = "decisions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    meeting_id = Column(String(36), ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False, index=True)
    description = Column(Text, nullable=False)
    speaker = Column(String(100), nullable=True)
    timestamp = Column(Float, nullable=True)  # in seconds
    evidence = Column(Text, nullable=True)
    confidence = Column(Float, default=0.0)
    validation_status = Column(String(50), default="unverified")  # verified, unverified, flagged

    meeting = relationship("Meeting", back_populates="decisions")


class ActionItem(Base):
    __tablename__ = "action_items"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    meeting_id = Column(String(36), ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False, index=True)
    task = Column(Text, nullable=False)
    owner = Column(String(150), default="Not specified", nullable=True)
    deadline = Column(String(150), default="Not specified", nullable=True)
    timestamp = Column(Float, nullable=True)  # in seconds
    evidence = Column(Text, nullable=True)
    status = Column(String(50), default="pending")  # pending, completed
    confidence = Column(Float, default=0.0)
    validation_status = Column(String(50), default="unverified")  # verified, unverified, flagged

    meeting = relationship("Meeting", back_populates="action_items")
