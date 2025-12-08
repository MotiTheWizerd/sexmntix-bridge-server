"""Switch embeddings to gemini-embedding-001 (1536 dims)"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "8f1b3f3f5a2c"
down_revision = "dd081c7166ea"
branch_labels = None
depends_on = None


def _drop_embedding_indexes():
    op.execute("DROP INDEX IF EXISTS memory_logs_embedding_hnsw_cosine_idx")
    op.execute("DROP INDEX IF EXISTS mental_notes_embedding_hnsw_cosine_idx")


def _create_embedding_indexes():
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS memory_logs_embedding_hnsw_cosine_idx
        ON memory_logs USING hnsw (embedding vector_cosine_ops)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS mental_notes_embedding_hnsw_cosine_idx
        ON mental_notes USING hnsw (embedding vector_cosine_ops)
        """
    )


def upgrade():
    _drop_embedding_indexes()

    # Existing 768D vectors are incompatible with 1536D, so reset columns.
    op.execute("UPDATE memory_logs SET embedding = NULL")
    op.execute("UPDATE mental_notes SET embedding = NULL")
    op.execute("UPDATE conversations SET embedding = NULL")

    op.execute("ALTER TABLE memory_logs ALTER COLUMN embedding TYPE vector(1536)")
    op.execute("ALTER TABLE mental_notes ALTER COLUMN embedding TYPE vector(1536)")
    op.execute("ALTER TABLE conversations ALTER COLUMN embedding TYPE vector(1536)")

    _create_embedding_indexes()

    # Update embedding model defaults on users table
    op.execute(
        """
        UPDATE users
        SET embedding_model = 'models/gemini-embedding-001'
        WHERE embedding_model = 'models/text-embedding-004'
        """
    )
    op.alter_column(
        "users",
        "embedding_model",
        existing_type=sa.String(length=100),
        nullable=False,
        server_default=sa.text("'models/gemini-embedding-001'"),
    )


def downgrade():
    _drop_embedding_indexes()

    op.execute("UPDATE memory_logs SET embedding = NULL")
    op.execute("UPDATE mental_notes SET embedding = NULL")
    op.execute("UPDATE conversations SET embedding = NULL")

    op.execute("ALTER TABLE memory_logs ALTER COLUMN embedding TYPE vector(768)")
    op.execute("ALTER TABLE mental_notes ALTER COLUMN embedding TYPE vector(768)")
    op.execute("ALTER TABLE conversations ALTER COLUMN embedding TYPE vector(768)")

    _create_embedding_indexes()

    op.execute(
        """
        UPDATE users
        SET embedding_model = 'models/text-embedding-004'
        WHERE embedding_model = 'models/gemini-embedding-001'
        """
    )
    op.alter_column(
        "users",
        "embedding_model",
        existing_type=sa.String(length=100),
        nullable=False,
        server_default=sa.text("'models/text-embedding-004'"),
    )
