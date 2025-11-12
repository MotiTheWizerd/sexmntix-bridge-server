"""add_embedding_fields_to_memory_logs

Adds vector embedding support and user/project isolation to memory_logs table.

Fields added:
- embedding: ARRAY(Float) for storing 768D vector embeddings
- user_id: String(255) for user isolation in ChromaDB collections
- project_id: String(255) for project isolation in ChromaDB collections

Revision ID: fb1c8a41bc5d
Revises: f7f51aee3ffe
Create Date: 2025-11-13 00:33:39.009476

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'fb1c8a41bc5d'
down_revision: Union[str, None] = 'f7f51aee3ffe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add embedding field for vector storage (768 dimensions)
    op.add_column(
        'memory_logs',
        sa.Column('embedding', postgresql.ARRAY(sa.Float()), nullable=True)
    )

    # Add user_id for ChromaDB collection isolation
    op.add_column(
        'memory_logs',
        sa.Column('user_id', sa.String(length=255), nullable=True)
    )
    op.create_index(
        op.f('ix_memory_logs_user_id'),
        'memory_logs',
        ['user_id'],
        unique=False
    )

    # Add project_id for ChromaDB collection isolation
    op.add_column(
        'memory_logs',
        sa.Column('project_id', sa.String(length=255), nullable=True)
    )
    op.create_index(
        op.f('ix_memory_logs_project_id'),
        'memory_logs',
        ['project_id'],
        unique=False
    )


def downgrade() -> None:
    # Remove indexes
    op.drop_index(op.f('ix_memory_logs_project_id'), table_name='memory_logs')
    op.drop_index(op.f('ix_memory_logs_user_id'), table_name='memory_logs')

    # Remove columns
    op.drop_column('memory_logs', 'project_id')
    op.drop_column('memory_logs', 'user_id')
    op.drop_column('memory_logs', 'embedding')
