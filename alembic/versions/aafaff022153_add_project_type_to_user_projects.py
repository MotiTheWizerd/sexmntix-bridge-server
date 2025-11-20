"""add_project_type_to_user_projects

Revision ID: aafaff022153
Revises: 3723fae248ef
Create Date: 2025-11-20 22:13:04.590139

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aafaff022153'
down_revision: Union[str, None] = '3723fae248ef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the ENUM type
    op.execute("CREATE TYPE projecttype AS ENUM ('vscode', 'general')")

    # Add the project_type column with default value
    op.execute("""
        ALTER TABLE user_projects
        ADD COLUMN project_type projecttype NOT NULL DEFAULT 'vscode'
    """)


def downgrade() -> None:
    # Drop the column
    op.execute("ALTER TABLE user_projects DROP COLUMN project_type")

    # Drop the ENUM type
    op.execute("DROP TYPE projecttype")
