"""
ORM model definitions for core entities.

This module defines the minimal schema for meetings and utterances
that will be expanded in later phases.
"""

from sqlalchemy import Column, String, DateTime, Integer, Text, ForeignKey
# from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .db import Base
import uuid
from datetime import datetime

def _uuid_str() -> str:
    """
    Generate a new UUID string.

    Returns:
        str: A fresh UUID value in string form.
    """
    return str(uuid.uuid4())

class Meeting(Base):
    """
    Represents a single meeting instance.

    Attributes:
        id (str): Primary key as a UUID string.
        title (str): Human-readable meeting title.
        meet_url (str): Google Meet URL or identifier.
        start_ts (datetime): Meeting start timestamp.
        end_ts (datetime | None): Meeting end timestamp.
    """
    __tablename__ = "meetings"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    title = Column(String(255), nullable=False, default="Untitled Meeting")
    meet_url = Column(Text, nullable=True)
    start_ts = Column(DateTime, default=datetime.utcnow, nullable=False)
    end_ts = Column(DateTime, nullable=True)

    utterances = relationship("Utterance", back_populates="meeting", cascade="all, delete-orphan")


class Utterance(Base):
    """
    Represents a time-aligned text segment from the meeting audio.

    Attributes:
        id (str): Primary key as a UUID string.
        meeting_id (str): Foreign key to the meeting.
        speaker_label (str): Optional speaker label (e.g., 'Speaker 1').
        t_start_ms (int): Start time of the segment in milliseconds.
        t_end_ms (int): End time of the segment in milliseconds.
        text (str): Transcribed content.
        lang (str | None): Language tag (e.g., 'en', 'hi', 'mixed').
    """
    __tablename__ = "utterances"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    meeting_id = Column(String(36), ForeignKey("meetings.id"), nullable=False)
    speaker_label = Column(String(64), nullable=True)
    t_start_ms = Column(Integer, nullable=False, default=0)
    t_end_ms = Column(Integer, nullable=False, default=0)
    text = Column(Text, nullable=False)
    lang = Column(String(16), nullable=True)

    meeting = relationship("Meeting", back_populates="utterances")
