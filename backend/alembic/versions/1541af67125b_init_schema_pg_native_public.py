"""init schema (pg-native, public)

Revision ID: 1541af67125b
Revises:
Create Date: 2025-08-18 00:44:48.976408
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "1541af67125b"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # meetings
    op.create_table(
        "meetings",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("meet_url", sa.Text(), nullable=True),
        sa.Column(
            "start_ts",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("end_ts", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="public",
    )

    # utterances
    op.create_table(
        "utterances",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("meeting_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("speaker_label", sa.String(length=64), nullable=True),
        sa.Column("start_time_ms", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("end_time_ms", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("lang", sa.String(length=16), nullable=True),
        sa.Column("is_final", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["meeting_id"], ["public.meetings.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="public",
    )

    # useful indexes
    op.create_index(
        "idx_utterances_meeting_time",
        "utterances",
        ["meeting_id", "start_time_ms"],
        unique=False,
        schema="public",
    )
    op.create_index(
        "idx_utterances_is_final",
        "utterances",
        ["is_final"],
        unique=False,
        schema="public",
    )

    # NOTE: removed the autogen "op.drop_table('alembic_version')" line.


def downgrade() -> None:
    op.drop_index("idx_utterances_is_final", table_name="utterances", schema="public")
    op.drop_index("idx_utterances_meeting_time", table_name="utterances", schema="public")
    op.drop_table("utterances", schema="public")
    op.drop_table("meetings", schema="public")