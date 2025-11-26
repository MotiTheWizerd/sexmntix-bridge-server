"""create retrieval_logs table

Revision ID: 6c4e3f9a3c21
Revises: 2c0a3d80f2a0
Create Date: 2025-11-26 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "6c4e3f9a3c21"
down_revision: Union[str, None] = "2c0a3d80f2a0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "retrieval_logs",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True, nullable=False),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("query", sa.Text(), nullable=True),
        sa.Column("user_id", sa.String(length=255), nullable=True),
        sa.Column("project_id", sa.String(length=255), nullable=True),
        sa.Column("session_id", sa.String(length=255), nullable=True),
        sa.Column("required_memory", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("results", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("results_count", sa.Integer(), nullable=True),
        sa.Column("limit", sa.Integer(), nullable=True),
        sa.Column("min_similarity", sa.Float(), nullable=True),
        sa.Column("target", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_retrieval_logs_user_id", "retrieval_logs", ["user_id"], unique=False)
    op.create_index("ix_retrieval_logs_project_id", "retrieval_logs", ["project_id"], unique=False)
    op.create_index("ix_retrieval_logs_request_id", "retrieval_logs", ["request_id"], unique=False)
    op.create_index("ix_retrieval_logs_target", "retrieval_logs", ["target"], unique=False)
    op.create_index("ix_retrieval_logs_created_at", "retrieval_logs", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_retrieval_logs_created_at", table_name="retrieval_logs")
    op.drop_index("ix_retrieval_logs_target", table_name="retrieval_logs")
    op.drop_index("ix_retrieval_logs_request_id", table_name="retrieval_logs")
    op.drop_index("ix_retrieval_logs_project_id", table_name="retrieval_logs")
    op.drop_index("ix_retrieval_logs_user_id", table_name="retrieval_logs")
    op.drop_table("retrieval_logs")
