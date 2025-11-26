"""create icm_logs table

Revision ID: 2c0a3d80f2a0
Revises: 41fb92ae77b8
Create Date: 2025-11-26 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "2c0a3d80f2a0"
down_revision: Union[str, None] = "41fb92ae77b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "icm_logs",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True, nullable=False),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("icm_type", sa.String(length=32), nullable=False),
        sa.Column("query", sa.Text(), nullable=True),
        sa.Column("user_id", sa.String(length=255), nullable=True),
        sa.Column("project_id", sa.String(length=255), nullable=True),
        sa.Column("session_id", sa.String(length=255), nullable=True),
        sa.Column("retrieval_strategy", sa.String(length=64), nullable=True),
        sa.Column("required_memory", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("time_window_start", sa.DateTime(), nullable=True),
        sa.Column("time_window_end", sa.DateTime(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("results_count", sa.Integer(), nullable=True),
        sa.Column("limit", sa.Integer(), nullable=True),
        sa.Column("min_similarity", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_icm_logs_user_id", "icm_logs", ["user_id"], unique=False)
    op.create_index("ix_icm_logs_project_id", "icm_logs", ["project_id"], unique=False)
    op.create_index("ix_icm_logs_icm_type", "icm_logs", ["icm_type"], unique=False)
    op.create_index("ix_icm_logs_created_at", "icm_logs", ["created_at"], unique=False)
    op.create_index("ix_icm_logs_request_id", "icm_logs", ["request_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_icm_logs_request_id", table_name="icm_logs")
    op.drop_index("ix_icm_logs_created_at", table_name="icm_logs")
    op.drop_index("ix_icm_logs_icm_type", table_name="icm_logs")
    op.drop_index("ix_icm_logs_project_id", table_name="icm_logs")
    op.drop_index("ix_icm_logs_user_id", table_name="icm_logs")
    op.drop_table("icm_logs")
