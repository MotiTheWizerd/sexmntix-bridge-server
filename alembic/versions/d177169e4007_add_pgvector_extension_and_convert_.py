"""add_pgvector_extension_and_convert_embeddings

Revision ID: d177169e4007
Revises: f26216369632
Create Date: 2025-11-16 05:08:23.578609

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd177169e4007'
down_revision: Union[str, None] = 'f26216369632'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if pgvector extension is available before attempting to use it
    # We use a raw connection to check without failing the transaction
    connection = op.get_bind()

    # Check if vector extension is available
    result = connection.execute(sa.text(
        "SELECT COUNT(*) FROM pg_available_extensions WHERE name = 'vector'"
    ))
    vector_available = result.scalar() > 0

    if not vector_available:
        print("⚠ pgvector extension not available on this PostgreSQL server")
        print("  Skipping vector operations - embeddings will remain as ARRAY(Float)")
        print("  To enable pgvector later, install the extension and re-run this migration")
        return

    # pgvector is available, proceed with installation and conversion
    try:
        # Step 1: Install pgvector extension
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")

        # Step 2: Convert memory_logs.embedding from ARRAY(Float) to vector(768)
        # First, we need to handle the conversion carefully
        op.execute("""
            ALTER TABLE memory_logs
            ALTER COLUMN embedding TYPE vector(768)
            USING CASE
                WHEN embedding IS NULL THEN NULL
                ELSE embedding::vector(768)
            END
        """)

        # Step 3: Create HNSW index on memory_logs.embedding for fast similarity search
        # Using cosine distance as the default distance metric
        op.execute("""
            CREATE INDEX IF NOT EXISTS memory_logs_embedding_hnsw_cosine_idx
            ON memory_logs
            USING hnsw (embedding vector_cosine_ops)
        """)

        # Step 4: Convert mental_notes.embedding from ARRAY(Float) to vector(768)
        op.execute("""
            ALTER TABLE mental_notes
            ALTER COLUMN embedding TYPE vector(768)
            USING CASE
                WHEN embedding IS NULL THEN NULL
                ELSE embedding::vector(768)
            END
        """)

        # Step 5: Create HNSW index on mental_notes.embedding
        op.execute("""
            CREATE INDEX IF NOT EXISTS mental_notes_embedding_hnsw_cosine_idx
            ON mental_notes
            USING hnsw (embedding vector_cosine_ops)
        """)

        print("✓ pgvector extension enabled and embeddings converted to vector(768)")
    except Exception as e:
        print(f"⚠ Error during pgvector operations: {str(e)}")
        raise


def downgrade() -> None:
    # Drop HNSW indexes
    op.execute("DROP INDEX IF EXISTS mental_notes_embedding_hnsw_cosine_idx")
    op.execute("DROP INDEX IF EXISTS memory_logs_embedding_hnsw_cosine_idx")

    # Convert vector(768) back to ARRAY(Float)
    op.execute("""
        ALTER TABLE mental_notes
        ALTER COLUMN embedding TYPE float[]
        USING CASE
            WHEN embedding IS NULL THEN NULL
            ELSE embedding::float[]
        END
    """)

    op.execute("""
        ALTER TABLE memory_logs
        ALTER COLUMN embedding TYPE float[]
        USING CASE
            WHEN embedding IS NULL THEN NULL
            ELSE embedding::float[]
        END
    """)

    # Note: We don't drop the vector extension in downgrade as it might be used by other tables
    # If needed, manually run: DROP EXTENSION IF EXISTS vector CASCADE
