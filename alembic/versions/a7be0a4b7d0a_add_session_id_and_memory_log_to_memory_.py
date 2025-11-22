"""add_session_id_and_memory_log_to_memory_logs

Revision ID: a7be0a4b7d0a
Revises: b94261ba8b2a
Create Date: 2025-11-22 20:43:45.878611

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'a7be0a4b7d0a'
down_revision: Union[str, None] = 'b94261ba8b2a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add session_id column (nullable for now, will be populated in next migration)
    op.add_column('memory_logs', sa.Column('session_id', sa.String(255), nullable=True))

    # Add memory_log JSONB column (nullable for now, will be populated in next migration)
    op.add_column('memory_logs', sa.Column('memory_log', postgresql.JSONB(), nullable=True))

    # Add index on session_id for faster queries
    op.create_index('ix_memory_logs_session_id', 'memory_logs', ['session_id'])


def downgrade() -> None:
    # Drop index
    op.drop_index('ix_memory_logs_session_id', 'memory_logs')

    # Drop columns
    op.drop_column('memory_logs', 'memory_log')
    op.drop_column('memory_logs', 'session_id')
