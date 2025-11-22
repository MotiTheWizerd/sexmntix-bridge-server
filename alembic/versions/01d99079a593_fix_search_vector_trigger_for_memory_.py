"""fix_search_vector_trigger_for_memory_log_column

Updates the search_vector trigger function to use 'memory_log' column instead of 'raw_data'.
The raw_data column was renamed to memory_log in a previous migration.

Revision ID: 01d99079a593
Revises: 6765996ce4bf
Create Date: 2025-11-23 00:06:29.377157

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '01d99079a593'
down_revision: Union[str, None] = '6765996ce4bf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Update search_vector trigger to use memory_log instead of raw_data."""

    # Recreate function to use memory_log column instead of raw_data
    op.execute("""
        CREATE OR REPLACE FUNCTION update_memory_log_search_vector()
        RETURNS TRIGGER AS $$
        BEGIN
            -- Extract searchable text fields from memory_log JSONB (renamed from raw_data)
            NEW.search_vector :=
                setweight(to_tsvector('english', COALESCE(NEW.task, '')), 'A') ||
                setweight(to_tsvector('english', COALESCE(NEW.memory_log->>'summary', '')), 'A') ||
                setweight(to_tsvector('english', COALESCE(NEW.memory_log->>'root_cause', '')), 'B') ||
                setweight(to_tsvector('english', COALESCE(NEW.memory_log->>'lesson', '')), 'B') ||
                setweight(to_tsvector('english', COALESCE(NEW.memory_log->>'component', '')), 'C') ||
                setweight(to_tsvector('english', COALESCE(NEW.memory_log->>'validation', '')), 'C') ||
                setweight(to_tsvector('english', COALESCE(
                    array_to_string(
                        ARRAY(SELECT jsonb_array_elements_text(NEW.memory_log->'tags')),
                        ' '
                    ), ''
                )), 'D');

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)


def downgrade() -> None:
    """Revert search_vector trigger to use raw_data."""

    # Recreate original function that used raw_data
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

