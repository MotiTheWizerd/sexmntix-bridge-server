"""add_session_id_to_conversations

Revision ID: 05720a04eccc
Revises: 1c4525efa9cc
Create Date: 2025-11-20 19:59:53.870694

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '05720a04eccc'
down_revision: Union[str, None] = '1c4525efa9cc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add session_id column to conversations table
    op.add_column('conversations', sa.Column('session_id', sa.String(length=255), nullable=True))
    op.create_index(op.f('ix_conversations_session_id'), 'conversations', ['session_id'], unique=False)


def downgrade() -> None:
    # Remove session_id column from conversations table
    op.drop_index(op.f('ix_conversations_session_id'), table_name='conversations')
    op.drop_column('conversations', 'session_id')
