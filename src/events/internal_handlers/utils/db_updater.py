"""
PostgreSQL embedding update operations.

Handles updating PostgreSQL records with embeddings after
ChromaDB storage succeeds, with non-blocking failure handling.
"""

from typing import List, Callable
from src.modules.core import Logger
from src.database.repositories import MemoryLogRepository, MentalNoteRepository, ConversationRepository


class DatabaseEmbeddingUpdater:
    """Updates PostgreSQL records with embeddings"""

    def __init__(
        self,
        db_session_factory: Callable,
        logger: Logger
    ):
        """
        Initialize database updater.

        Args:
            db_session_factory: Callable returning AsyncSession for PostgreSQL
            logger: Logger instance
        """
        self.db_session_factory = db_session_factory
        self.logger = logger

    async def update_memory_log(
        self,
        memory_log_id: int,
        embedding: List[float]
    ) -> bool:
        """
        Update memory log with embedding (non-blocking).

        Args:
            memory_log_id: Memory log ID
            embedding: Embedding vector

        Returns:
            True if successful, False if failed
        """
        try:
            async with self.db_session_factory() as db:
                repo = MemoryLogRepository(db)
                await repo.update(
                    id=memory_log_id,
                    embedding=embedding
                )
                await db.commit()
                return True
        except Exception as e:
            # Non-blocking: ChromaDB storage succeeded, PostgreSQL update failed
            # This is acceptable for batch processing where records may not exist in DB
            self.logger.warning(
                f"PostgreSQL update failed for memory_log {memory_log_id}: {e}. "
                f"Vector storage in ChromaDB succeeded."
            )
            return False

    async def update_mental_note(
        self,
        mental_note_id: int,
        embedding: List[float],
        user_id: str,
        project_id: str
    ) -> bool:
        """
        Update mental note with embedding (non-blocking).

        Args:
            mental_note_id: Mental note ID
            embedding: Embedding vector
            user_id: User identifier
            project_id: Project identifier

        Returns:
            True if successful, False if failed
        """
        try:
            async with self.db_session_factory() as db:
                repo = MentalNoteRepository(db)
                await repo.update(
                    id=mental_note_id,
                    embedding=embedding,
                    user_id=user_id,
                    project_id=project_id
                )
                await db.commit()
                return True
        except Exception as e:
            # Non-blocking: ChromaDB storage succeeded, PostgreSQL update failed
            self.logger.warning(
                f"PostgreSQL update failed for mental_note {mental_note_id}: {e}. "
                f"Vector storage in ChromaDB succeeded."
            )
            return False

    async def update_conversation(
        self,
        conversation_db_id: int,
        embedding: List[float]
    ) -> bool:
        """
        Update conversation with embedding (non-blocking).

        Args:
            conversation_db_id: Conversation database ID
            embedding: Embedding vector

        Returns:
            True if successful, False if failed
        """
        try:
            async with self.db_session_factory() as db:
                repo = ConversationRepository(db)
                await repo.update(
                    id=conversation_db_id,
                    embedding=embedding
                )
                await db.commit()
                return True
        except Exception as e:
            # Non-blocking: ChromaDB storage succeeded, PostgreSQL update failed
            self.logger.warning(
                f"PostgreSQL update failed for conversation {conversation_db_id}: {e}. "
                f"Vector storage in ChromaDB succeeded."
            )
            return False
