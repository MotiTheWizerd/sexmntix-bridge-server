"""rename_to_users_project_vscode_and_remove_project_type

Revision ID: 864ce1b2f83f
Revises: aafaff022153
Create Date: 2025-11-21 21:17:19.440257

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '864ce1b2f83f'
down_revision: Union[str, None] = 'aafaff022153'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: Drop the project_type column
    op.execute("ALTER TABLE user_projects DROP COLUMN project_type")

    # Step 2: Rename the table
    op.execute("ALTER TABLE user_projects RENAME TO users_project_vscode")

    # Step 3: Drop the projecttype enum (no longer needed)
    op.execute("DROP TYPE projecttype")


def downgrade() -> None:
    # Step 1: Recreate the enum
    op.execute("CREATE TYPE projecttype AS ENUM ('vscode', 'general')")

    # Step 2: Rename table back
    op.execute("ALTER TABLE users_project_vscode RENAME TO user_projects")

    # Step 3: Re-add the project_type column with default value
    op.execute("""
        ALTER TABLE user_projects
        ADD COLUMN project_type projecttype NOT NULL DEFAULT 'vscode'
    """)
