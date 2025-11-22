"""migrate_memory_logs_data_to_new_schema

Revision ID: 660e1eb9ed45
Revises: a7be0a4b7d0a
Create Date: 2025-11-22 20:54:50.283090

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '660e1eb9ed45'
down_revision: Union[str, None] = 'a7be0a4b7d0a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Migrate data from raw_data structure to new flat schema
    # Old structure: raw_data = {user_id, project_id, session_id, datetime, memory_log: {...}}
    # New structure: memory_log column = {...} (the inner memory_log object)

    connection = op.get_bind()

    # Update all existing records
    connection.execute(sa.text("""
        UPDATE memory_logs
        SET
            session_id = raw_data->>'session_id',
            memory_log = raw_data->'memory_log'
        WHERE raw_data IS NOT NULL
    """))

    print("SUCCESS: Data migration completed: raw_data structure flattened to memory_log column")


def downgrade() -> None:
    # Restore the original raw_data structure
    connection = op.get_bind()

    connection.execute(sa.text("""
        UPDATE memory_logs
        SET raw_data = jsonb_build_object(
            'user_id', user_id,
            'project_id', project_id,
            'session_id', session_id,
            'datetime', created_at::text,
            'memory_log', memory_log
        )
        WHERE memory_log IS NOT NULL
    """))

    # Clear the new columns
    connection.execute(sa.text("""
        UPDATE memory_logs
        SET
            session_id = NULL,
            memory_log = NULL
    """))
