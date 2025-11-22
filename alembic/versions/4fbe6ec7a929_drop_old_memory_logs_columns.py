"""drop_old_memory_logs_columns

Revision ID: 4fbe6ec7a929
Revises: 660e1eb9ed45
Create Date: 2025-11-22 20:57:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '4fbe6ec7a929'
down_revision: Union[str, None] = '660e1eb9ed45'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the old 'date' column (replaced by created_at)
    op.drop_column('memory_logs', 'date')

    # Drop the old 'raw_data' column (replaced by memory_log)
    op.drop_column('memory_logs', 'raw_data')

    print("SUCCESS: Dropped old columns: date, raw_data")


def downgrade() -> None:
    # Restore the old columns
    op.add_column('memory_logs', sa.Column('date', sa.DateTime(), nullable=True))
    op.add_column('memory_logs', sa.Column('raw_data', postgresql.JSONB(), nullable=True))

    # Restore indexes
    op.create_index('ix_memory_logs_date', 'memory_logs', ['date'])
