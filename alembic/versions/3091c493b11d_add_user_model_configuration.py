"""add_user_model_configuration

Revision ID: 3091c493b11d
Revises: 421aec1a864d
Create Date: 2025-11-19 21:19:04.299699

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '3091c493b11d'
down_revision: Union[str, None] = '421aec1a864d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add foreground_model column
    op.add_column('users', sa.Column(
        'foreground_model',
        sa.String(length=100),
        nullable=False,
        server_default='gpt-4'
    ))
    
    # Add background_workers JSONB column
    op.add_column('users', sa.Column(
        'background_workers',
        postgresql.JSONB(astext_type=sa.Text()),
        nullable=False,
        server_default='{"memory_synthesizer": {"provider": "google", "model": "gemini-2.0-flash", "enabled": true}}'
    ))
    
    # Add embedding_model column
    op.add_column('users', sa.Column(
        'embedding_model',
        sa.String(length=100),
        nullable=False,
        server_default='models/text-embedding-004'
    ))


def downgrade() -> None:
    # Remove columns in reverse order
    op.drop_column('users', 'embedding_model')
    op.drop_column('users', 'background_workers')
    op.drop_column('users', 'foreground_model')
