"""merge_heads

Revision ID: 4e4ae980dfbc
Revises: convert_user_id_uuid, d177169e4007
Create Date: 2025-11-17 22:07:38.616287

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4e4ae980dfbc'
down_revision: Union[str, None] = ('convert_user_id_uuid', 'd177169e4007')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
