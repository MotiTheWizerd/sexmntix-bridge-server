"""add_memory_logs_constraints

Revision ID: 6765996ce4bf
Revises: 4fbe6ec7a929
Create Date: 2025-11-22 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6765996ce4bf'
down_revision: Union[str, None] = '4fbe6ec7a929'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Make memory_log NOT NULL now that data has been migrated
    op.alter_column('memory_logs', 'memory_log',
                    existing_type=sa.dialects.postgresql.JSONB(),
                    nullable=False)

    print("SUCCESS: Added NOT NULL constraint to memory_log column")


def downgrade() -> None:
    # Make memory_log nullable again
    op.alter_column('memory_logs', 'memory_log',
                    existing_type=sa.dialects.postgresql.JSONB(),
                    nullable=True)
