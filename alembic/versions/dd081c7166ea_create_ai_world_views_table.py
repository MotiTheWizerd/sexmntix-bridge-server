"""create_ai_world_views_table

Revision ID: dd081c7166ea
Revises: 41232c6709aa
Create Date: 2025-12-06 00:59:47.465477

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dd081c7166ea'
down_revision: Union[str, None] = '41232c6709aa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create ai_world_views table for storing core beliefs and identity summaries.
    """
    op.create_table('ai_world_views',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('user_id', sa.dialects.postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('project_id', sa.dialects.postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('core_beliefs', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for efficient querying
    op.create_index(op.f('ix_ai_world_views_user_id'), 'ai_world_views', ['user_id'], unique=False)
    op.create_index(op.f('ix_ai_world_views_project_id'), 'ai_world_views', ['project_id'], unique=False)
    
    # Create composite unique constraint for user_id + project_id
    op.create_index('ix_ai_world_views_user_project', 'ai_world_views', ['user_id', 'project_id'], unique=True)


def downgrade() -> None:
    """
    Remove ai_world_views table and all associated indexes.
    """
    op.drop_index('ix_ai_world_views_user_project', table_name='ai_world_views')
    op.drop_index(op.f('ix_ai_world_views_project_id'), table_name='ai_world_views')
    op.drop_index(op.f('ix_ai_world_views_user_id'), table_name='ai_world_views')
    op.drop_table('ai_world_views')
