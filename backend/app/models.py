"""
ORM model definitions for core entities (Postgres-native).

- UUID primary keys (server-generated via gen_random_uuid())
- TIMESTAMPTZ for timestamps
- BIGINT for millisecond offsets
- CASCADE delete from meetings -> utterances
"""

from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, BigInteger, Boolean, text as sa_text
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import relationship, Mapped, mapped_column
from .db import Base


class Meeting(Base):
    __tablename__ = "meetings"

    # Keep Python type as str (uuid stored in DB)
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=sa_text("gen_random_uuid()"),
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False, default="Untitled Meeting")
    meet_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # timezone-aware timestamps
    start_ts: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa_text("now()"),
    )
    end_ts: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )

    utterances = relationship(
        "Utterance",
        back_populates="meeting",
        cascade="all, delete-orphan",
        passive_deletes=True,  # required for ON DELETE CASCADE to be efficient
    )


class Utterance(Base):
    __tablename__ = "utterances"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=sa_text("gen_random_uuid()"),
    )

    meeting_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("meetings.id", ondelete="CASCADE"),
        nullable=False,
    )

    speaker_label: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # millisecond timeline
    start_time_ms: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    end_time_ms: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)

    # keep column name 'text' in DB; alias sa_text for defaults to avoid collision
    text: Mapped[str] = mapped_column(Text, nullable=False)
    lang: Mapped[str | None] = mapped_column(String(16), nullable=True)

    # streaming/finality + audit
    is_final: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=sa_text("now()")
    )

    meeting = relationship("Meeting", back_populates="utterances")