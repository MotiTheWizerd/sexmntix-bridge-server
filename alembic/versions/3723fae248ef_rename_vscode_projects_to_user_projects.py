"""rename_vscode_projects_to_user_projects

Revision ID: 3723fae248ef
Revises: 05720a04eccc
Create Date: 2025-11-20 21:38:15.806786

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3723fae248ef'
down_revision: Union[str, None] = '05720a04eccc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename table from vscode_projects to user_projects
    op.rename_table('vscode_projects', 'user_projects')


def downgrade() -> None:
    # Rename table back from user_projects to vscode_projects
    op.rename_table('user_projects', 'vscode_projects')
