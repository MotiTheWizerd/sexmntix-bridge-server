"""Convert user id from integer to UUID

Revision ID: convert_user_id_uuid
Revises: d4c173fcc6ab
Create Date: 2025-11-17 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision: str = 'convert_user_id_uuid'
down_revision: Union[str, None] = 'd4c173fcc6ab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Convert users.id from Integer to UUID.

    Strategy:
    1. Enable UUID extension
    2. Add new uuid_id column
    3. Generate UUIDs for existing users and update references
    4. Drop old id column
    5. Rename uuid_id to id
    6. Add primary key constraint
    """

    # Step 1: Enable UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # Step 2: Add new uuid_id column
    op.add_column('users', sa.Column('uuid_id', postgresql.UUID(as_uuid=False), nullable=True))

    # Step 3: Generate UUIDs for existing users and create mapping
    # First, fetch existing users and generate UUIDs
    connection = op.get_bind()
    result = connection.execute(sa.text("SELECT id FROM users ORDER BY id"))
    user_mappings = {}

    for row in result:
        old_id = row[0]
        new_uuid = str(uuid.uuid4())
        user_mappings[old_id] = new_uuid

        # Update users table with new UUID
        connection.execute(
            sa.text("UPDATE users SET uuid_id = :uuid WHERE id = :old_id"),
            {"uuid": new_uuid, "old_id": old_id}
        )

    # Step 4: Update all references in other tables (user_id as String)
    # Update conversations table
    for old_id, new_uuid in user_mappings.items():
        connection.execute(
            sa.text("UPDATE conversations SET user_id = :new_uuid WHERE user_id = :old_id"),
            {"new_uuid": new_uuid, "old_id": str(old_id)}
        )

    # Update memory_logs table
    for old_id, new_uuid in user_mappings.items():
        connection.execute(
            sa.text("UPDATE memory_logs SET user_id = :new_uuid WHERE user_id = :old_id"),
            {"new_uuid": new_uuid, "old_id": str(old_id)}
        )

    # Update mental_notes table
    for old_id, new_uuid in user_mappings.items():
        connection.execute(
            sa.text("UPDATE mental_notes SET user_id = :new_uuid WHERE user_id = :old_id"),
            {"new_uuid": new_uuid, "old_id": str(old_id)}
        )

    # Step 5: Make uuid_id NOT NULL
    op.alter_column('users', 'uuid_id', nullable=False)

    # Step 6: Drop old id column
    op.drop_column('users', 'id')

    # Step 7: Rename uuid_id to id
    op.alter_column('users', 'uuid_id', new_column_name='id')

    # Step 8: Add primary key constraint
    op.create_primary_key('pk_users_id', 'users', ['id'])

    print(f"\n✅ Migrated {len(user_mappings)} users from Integer IDs to UUIDs")
    print("ID Mapping:")
    for old_id, new_uuid in user_mappings.items():
        print(f"  {old_id} → {new_uuid}")


def downgrade() -> None:
    """
    Downgrade is not supported for this migration as it would require
    maintaining the original integer IDs, which would be lost.

    If you need to rollback, restore from a backup.
    """
    raise NotImplementedError(
        "Downgrade from UUID to Integer is not supported. "
        "Restore from backup if needed."
    )
