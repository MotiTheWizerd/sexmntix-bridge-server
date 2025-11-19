"""remove_foreground_model_column

Revision ID: 0262664a5929
Revises: 8d681896b555
Create Date: 2025-11-19 22:48:00.409323

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0262664a5929'
down_revision: Union[str, None] = '8d681896b555'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Remove foreground_model column from users table
    op.drop_column('users', 'foreground_model')


def downgrade() -> None:
    # Re-add foreground_model column if rolling back
    op.add_column('users', sa.Column(
        'foreground_model',
        sa.String(length=100),
        nullable=False,
        server_default='gpt-4'
    ))
