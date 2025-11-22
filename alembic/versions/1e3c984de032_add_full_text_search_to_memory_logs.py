"""add_full_text_search_to_memory_logs

Adds PostgreSQL full-text search capabilities to memory_logs table for hybrid search.

Fields added:
- search_vector: TSVECTOR for full-text search indexing
- GIN index on search_vector for fast text search
- Trigger to auto-update search_vector on insert/update

This enables hybrid search combining vector similarity (70%) + keyword matching (30%).

Revision ID: 1e3c984de032
Revises: 864ce1b2f83f
Create Date: 2025-11-22 00:46:47.839667

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '1e3c984de032'
down_revision: Union[str, None] = '864ce1b2f83f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add full-text search support to memory_logs table."""

    # Add search_vector column (TSVECTOR type for full-text search)
    op.add_column(
        'memory_logs',
        sa.Column('search_vector', postgresql.TSVECTOR, nullable=True)
    )

    # Create GIN index for fast full-text search
    op.execute("""
        CREATE INDEX ix_memory_logs_search_vector
        ON memory_logs
        USING GIN(search_vector);
    """)

    # Create function to update search_vector from raw_data
    op.execute("""
        CREATE OR REPLACE FUNCTION update_memory_log_search_vector()
        RETURNS TRIGGER AS $$
        BEGIN
            -- Extract searchable text fields from raw_data JSONB
            NEW.search_vector :=
                setweight(to_tsvector('english', COALESCE(NEW.task, '')), 'A') ||
                setweight(to_tsvector('english', COALESCE(NEW.raw_data->>'summary', '')), 'A') ||
                setweight(to_tsvector('english', COALESCE(NEW.raw_data->>'root_cause', '')), 'B') ||
                setweight(to_tsvector('english', COALESCE(NEW.raw_data->>'lesson', '')), 'B') ||
                setweight(to_tsvector('english', COALESCE(NEW.raw_data->>'component', '')), 'C') ||
                setweight(to_tsvector('english', COALESCE(NEW.raw_data->>'validation', '')), 'C') ||
                setweight(to_tsvector('english', COALESCE(
                    array_to_string(
                        ARRAY(SELECT jsonb_array_elements_text(NEW.raw_data->'tags')),
                        ' '
                    ), ''
                )), 'D');

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Create trigger to auto-update search_vector
    op.execute("""
        CREATE TRIGGER memory_logs_search_vector_update
        BEFORE INSERT OR UPDATE ON memory_logs
        FOR EACH ROW
        EXECUTE FUNCTION update_memory_log_search_vector();
    """)

    # Backfill existing records with search_vector
    # This will use the trigger function to populate search_vector for all existing rows
    op.execute("""
        UPDATE memory_logs
        SET task = task
        WHERE search_vector IS NULL;
    """)


def downgrade() -> None:
    """Remove full-text search support from memory_logs table."""

    # Drop trigger
    op.execute("DROP TRIGGER IF EXISTS memory_logs_search_vector_update ON memory_logs;")

    # Drop function
    op.execute("DROP FUNCTION IF EXISTS update_memory_log_search_vector();")

    # Drop index
    op.execute("DROP INDEX IF EXISTS ix_memory_logs_search_vector;")

    # Drop column
    op.drop_column('memory_logs', 'search_vector')
