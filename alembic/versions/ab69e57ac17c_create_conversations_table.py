"""create_conversations_table

Revision ID: ab69e57ac17c
Revises: f26216369632
Create Date: 2025-11-16 XX:XX:XX.XXXXXX

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'ab69e57ac17c'
down_revision: Union[str, None] = 'f26216369632'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create conversations table WITHOUT pgvector dependency.

    Vector embeddings are stored ONLY in ChromaDB (conversations_{hash} collection),
    not in PostgreSQL. This avoids pgvector dependency while maintaining full
    semantic search capabilities via ChromaDB.
    """
    # Create conversations table (NO embedding column)
    op.create_table('conversations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('conversation_id', sa.String(length=255), nullable=False),
        sa.Column('model', sa.String(length=100), nullable=False),
        sa.Column('raw_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=True),
        sa.Column('project_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for efficient querying
    op.create_index(op.f('ix_conversations_conversation_id'), 'conversations', ['conversation_id'], unique=True)
    op.create_index(op.f('ix_conversations_model'), 'conversations', ['model'], unique=False)
    op.create_index(op.f('ix_conversations_user_id'), 'conversations', ['user_id'], unique=False)
    op.create_index(op.f('ix_conversations_project_id'), 'conversations', ['project_id'], unique=False)


def downgrade() -> None:
    """
    Remove conversations table and all associated indexes.
    """
    # Drop regular indexes
    op.drop_index(op.f('ix_conversations_project_id'), table_name='conversations')
    op.drop_index(op.f('ix_conversations_user_id'), table_name='conversations')
    op.drop_index(op.f('ix_conversations_model'), table_name='conversations')
    op.drop_index(op.f('ix_conversations_conversation_id'), table_name='conversations')

    # Drop table
    op.drop_table('conversations')
