"""update_background_workers_structure

Revision ID: 8d681896b555
Revises: 3091c493b11d
Create Date: 2025-11-19 21:34:05.384278

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8d681896b555'
down_revision: Union[str, None] = '3091c493b11d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Update existing users' background_workers to include both agents
    op.execute("""
        UPDATE users
        SET background_workers = jsonb_build_object(
            'conversation_analyzer', jsonb_build_object(
                'provider', 'google',
                'model', 'gemini-2.0-flash',
                'enabled', true
            ),
            'memory_synthesizer', jsonb_build_object(
                'provider', 'google',
                'model', 'gemini-2.0-flash',
                'enabled', true
            )
        )
        WHERE background_workers = '{"memory_synthesizer": {"provider": "google", "model": "gemini-2.0-flash", "enabled": true}}'::jsonb
    """)


def downgrade() -> None:
    # Revert to single memory_synthesizer agent
    op.execute("""
        UPDATE users
        SET background_workers = jsonb_build_object(
            'memory_synthesizer', jsonb_build_object(
                'provider', 'google',
                'model', 'gemini-2.0-flash',
                'enabled', true
            )
        )
        WHERE background_workers ? 'conversation_analyzer'
    """)
