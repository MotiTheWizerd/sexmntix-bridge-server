"""add_embedding_column_to_conversations

Revision ID: 41fb92ae77b8
Revises: 01d99079a593
Create Date: 2025-11-23 15:22:11.607612

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = '41fb92ae77b8'
down_revision: Union[str, None] = '01d99079a593'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add embedding column with pgvector Vector type (768 dimensions)
    # Column is nullable - will be NULL initially until population logic is implemented
    op.add_column('conversations', sa.Column('embedding', Vector(768), nullable=True))


def downgrade() -> None:
    # Remove embedding column
    op.drop_column('conversations', 'embedding')
