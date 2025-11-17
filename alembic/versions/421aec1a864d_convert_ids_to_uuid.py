"""convert_ids_to_uuid

Revision ID: 421aec1a864d
Revises: 4e4ae980dfbc
Create Date: 2025-11-17 22:07:52.011692

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '421aec1a864d'
down_revision: Union[str, None] = '4e4ae980dfbc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Convert integer IDs to UUIDs for memory_logs, mental_notes, and conversations tables."""

    # Enable uuid-ossp extension if not already enabled
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # --- memory_logs table ---
    # Add new UUID column
    op.add_column('memory_logs', sa.Column('id_new', postgresql.UUID(as_uuid=False), nullable=True))

    # Generate UUIDs for existing records
    op.execute('UPDATE memory_logs SET id_new = uuid_generate_v4()')

    # Make id_new not nullable
    op.alter_column('memory_logs', 'id_new', nullable=False)

    # Drop old primary key constraint
    op.execute('ALTER TABLE memory_logs DROP CONSTRAINT memory_logs_pkey')

    # Drop old id column
    op.drop_column('memory_logs', 'id')

    # Rename id_new to id
    op.alter_column('memory_logs', 'id_new', new_column_name='id')

    # Add primary key constraint
    op.create_primary_key('memory_logs_pkey', 'memory_logs', ['id'])

    # --- mental_notes table ---
    # Add new UUID column
    op.add_column('mental_notes', sa.Column('id_new', postgresql.UUID(as_uuid=False), nullable=True))

    # Generate UUIDs for existing records
    op.execute('UPDATE mental_notes SET id_new = uuid_generate_v4()')

    # Make id_new not nullable
    op.alter_column('mental_notes', 'id_new', nullable=False)

    # Drop old primary key constraint
    op.execute('ALTER TABLE mental_notes DROP CONSTRAINT mental_notes_pkey')

    # Drop old id column
    op.drop_column('mental_notes', 'id')

    # Rename id_new to id
    op.alter_column('mental_notes', 'id_new', new_column_name='id')

    # Add primary key constraint
    op.create_primary_key('mental_notes_pkey', 'mental_notes', ['id'])

    # --- conversations table ---
    # Add new UUID column
    op.add_column('conversations', sa.Column('id_new', postgresql.UUID(as_uuid=False), nullable=True))

    # Generate UUIDs for existing records
    op.execute('UPDATE conversations SET id_new = uuid_generate_v4()')

    # Make id_new not nullable
    op.alter_column('conversations', 'id_new', nullable=False)

    # Drop old primary key constraint
    op.execute('ALTER TABLE conversations DROP CONSTRAINT conversations_pkey')

    # Drop old id column
    op.drop_column('conversations', 'id')

    # Rename id_new to id
    op.alter_column('conversations', 'id_new', new_column_name='id')

    # Add primary key constraint
    op.create_primary_key('conversations_pkey', 'conversations', ['id'])


def downgrade() -> None:
    """Revert UUIDs back to integer IDs."""

    # --- memory_logs table ---
    # Add new integer column
    op.add_column('memory_logs', sa.Column('id_new', sa.Integer(), autoincrement=True, nullable=True))

    # Generate sequential integers for existing records
    op.execute('UPDATE memory_logs SET id_new = nextval(pg_get_serial_sequence(\'memory_logs\', \'id_new\'))')

    # Make id_new not nullable
    op.alter_column('memory_logs', 'id_new', nullable=False)

    # Drop old primary key constraint
    op.execute('ALTER TABLE memory_logs DROP CONSTRAINT memory_logs_pkey')

    # Drop old id column
    op.drop_column('memory_logs', 'id')

    # Rename id_new to id
    op.alter_column('memory_logs', 'id_new', new_column_name='id')

    # Add primary key constraint
    op.create_primary_key('memory_logs_pkey', 'memory_logs', ['id'])

    # --- mental_notes table ---
    # Add new integer column
    op.add_column('mental_notes', sa.Column('id_new', sa.Integer(), autoincrement=True, nullable=True))

    # Generate sequential integers for existing records
    op.execute('UPDATE mental_notes SET id_new = nextval(pg_get_serial_sequence(\'mental_notes\', \'id_new\'))')

    # Make id_new not nullable
    op.alter_column('mental_notes', 'id_new', nullable=False)

    # Drop old primary key constraint
    op.execute('ALTER TABLE mental_notes DROP CONSTRAINT mental_notes_pkey')

    # Drop old id column
    op.drop_column('mental_notes', 'id')

    # Rename id_new to id
    op.alter_column('mental_notes', 'id_new', new_column_name='id')

    # Add primary key constraint
    op.create_primary_key('mental_notes_pkey', 'mental_notes', ['id'])

    # --- conversations table ---
    # Add new integer column
    op.add_column('conversations', sa.Column('id_new', sa.Integer(), autoincrement=True, nullable=True))

    # Generate sequential integers for existing records
    op.execute('UPDATE conversations SET id_new = nextval(pg_get_serial_sequence(\'conversations\', \'id_new\'))')

    # Make id_new not nullable
    op.alter_column('conversations', 'id_new', nullable=False)

    # Drop old primary key constraint
    op.execute('ALTER TABLE conversations DROP CONSTRAINT conversations_pkey')

    # Drop old id column
    op.drop_column('conversations', 'id')

    # Rename id_new to id
    op.alter_column('conversations', 'id_new', new_column_name='id')

    # Add primary key constraint
    op.create_primary_key('conversations_pkey', 'conversations', ['id'])
