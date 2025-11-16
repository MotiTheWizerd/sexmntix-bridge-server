"""remove_unique_constraint_from_conversation_id

Revision ID: d4c173fcc6ab
Revises: ab69e57ac17c
Create Date: 2025-11-16 11:43:58.390907

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4c173fcc6ab'
down_revision: Union[str, None] = 'ab69e57ac17c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop unique index and constraint from conversation_id if they exist
    # This allows duplicate conversation_id values (for versioning/updates)

    # Drop the unique index created by unique=True in the model
    op.drop_index('ix_conversations_conversation_id', table_name='conversations')

    # Recreate as non-unique index for performance
    op.create_index('ix_conversations_conversation_id', 'conversations', ['conversation_id'], unique=False)


def downgrade() -> None:
    # Restore unique index on conversation_id
    op.drop_index('ix_conversations_conversation_id', table_name='conversations')
    op.create_index('ix_conversations_conversation_id', 'conversations', ['conversation_id'], unique=True)
