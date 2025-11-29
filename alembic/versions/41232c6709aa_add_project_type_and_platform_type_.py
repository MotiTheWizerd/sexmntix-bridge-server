"""add project_type and platform_type columns to users_project_vscode table

Revision ID: 41232c6709aa
Revises: 7f3c1a1a4d50
Create Date: 2025-11-29 23:29:46.563098

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '41232c6709aa'
down_revision: Union[str, None] = '7f3c1a1a4d50'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the ENUM types if they don't exist
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE projecttype AS ENUM ('vscode', 'vim', 'intellij', 'general');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE platformtype AS ENUM ('desktop', 'web', 'mobile', 'general');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Add the project_type column as nullable
    op.add_column('users_project_vscode', sa.Column('project_type', sa.Enum('vscode', 'vim', 'intellij', 'general', name='projecttype'), nullable=True))

    # Add the platform_type column as nullable
    op.add_column('users_project_vscode', sa.Column('platform_type', sa.Enum('desktop', 'web', 'mobile', 'general', name='platformtype'), nullable=True))


def downgrade() -> None:
    # Drop the columns
    op.drop_column('users_project_vscode', 'platform_type')
    op.drop_column('users_project_vscode', 'project_type')

    # Drop the ENUM types if they exist
    op.execute("DROP TYPE IF EXISTS platformtype")
    op.execute("DROP TYPE IF EXISTS projecttype")
