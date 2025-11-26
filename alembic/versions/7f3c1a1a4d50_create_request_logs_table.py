"""create request_logs table

Revision ID: 7f3c1a1a4d50
Revises: 6c4e3f9a3c21
Create Date: 2025-11-26 12:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "7f3c1a1a4d50"
down_revision: Union[str, None] = "6c4e3f9a3c21"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "request_logs",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True, nullable=False),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("path", sa.String(length=512), nullable=True),
        sa.Column("method", sa.String(length=16), nullable=True),
        sa.Column("user_id", sa.String(length=255), nullable=True),
        sa.Column("project_id", sa.String(length=255), nullable=True),
        sa.Column("session_id", sa.String(length=255), nullable=True),
        sa.Column("query_params", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("headers", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("body", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_request_logs_request_id", "request_logs", ["request_id"], unique=False)
    op.create_index("ix_request_logs_path", "request_logs", ["path"], unique=False)
    op.create_index("ix_request_logs_method", "request_logs", ["method"], unique=False)
    op.create_index("ix_request_logs_user_id", "request_logs", ["user_id"], unique=False)
    op.create_index("ix_request_logs_project_id", "request_logs", ["project_id"], unique=False)
    op.create_index("ix_request_logs_created_at", "request_logs", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_request_logs_created_at", table_name="request_logs")
    op.drop_index("ix_request_logs_project_id", table_name="request_logs")
    op.drop_index("ix_request_logs_user_id", table_name="request_logs")
    op.drop_index("ix_request_logs_method", table_name="request_logs")
    op.drop_index("ix_request_logs_path", table_name="request_logs")
    op.drop_index("ix_request_logs_request_id", table_name="request_logs")
    op.drop_table("request_logs")
