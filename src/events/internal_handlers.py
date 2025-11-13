"""
Internal event handlers for memory log storage.

These handlers respond to memory_log events and persist data
to PostgreSQL and ChromaDB, enabling event-driven architecture.
"""

from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.core import EventBus, Logger
from src.modules.embeddings import EmbeddingService
from src.database.repositories.memory_log_repository import MemoryLogRepository
from src.api.dependencies.vector_storage import create_vector_storage_service


class MemoryLogStorageHandlers:
    """
    Event handlers for memory log storage operations.

    Decouples vector storage from main request flow,
    allowing async background processing and non-blocking failures.

    With per-project isolation, creates VectorStorageService dynamically
    for each event based on user_id and project_id.
    """

    def __init__(
        self,
        db_session_factory,
        embedding_service: EmbeddingService,
        event_bus: EventBus,
        logger: Logger
    ):
        """
        Initialize storage handlers.

        Args:
            db_session_factory: Callable returning AsyncSession for PostgreSQL
            embedding_service: Service for generating embeddings
            event_bus: Event bus for publishing events
            logger: Logger instance
        """
        self.db_session_factory = db_session_factory
        self.embedding_service = embedding_service
        self.event_bus = event_bus
        self.logger = logger

    async def handle_memory_log_stored(self, event_data: Dict[str, Any]):
        """
        Handle memory_log.stored event for vector storage.

        Generates embeddings and stores in ChromaDB after PostgreSQL storage completes.

        Args:
            event_data: Event payload containing memory log data and ID
        """
        try:
            # Skip if user_id or project_id not provided
            user_id = event_data.get("user_id")
            project_id = event_data.get("project_id")
            memory_log_id = event_data.get("memory_log_id")

            if not user_id or not project_id:
                self.logger.warning(
                    f"Skipping vector storage: user_id or project_id not provided"
                )
                return

            if not memory_log_id:
                self.logger.error(
                    "Skipping vector storage: memory_log_id not found in event data"
                )
                return

            self.logger.info(
                f"Generating and storing vector for memory_log {memory_log_id} "
                f"(user: {user_id}, project: {project_id})"
            )

            # Create VectorStorageService for this specific user/project
            vector_service = create_vector_storage_service(
                user_id=user_id,
                project_id=project_id,
                embedding_service=self.embedding_service,
                event_bus=self.event_bus,
                logger=self.logger
            )

            # Generate embedding and store in ChromaDB
            memory_id, embedding = await vector_service.store_memory_vector(
                memory_log_id=memory_log_id,
                memory_data=event_data["raw_data"],
                user_id=user_id,
                project_id=project_id
            )

            # Update PostgreSQL with embedding (optional - may not exist in DB)
            try:
                async with self.db_session_factory() as db:
                    repo = MemoryLogRepository(db)
                    await repo.update(
                        id=memory_log_id,
                        embedding=embedding
                    )
                    await db.commit()
                    self.logger.info(f"PostgreSQL updated for memory_log {memory_log_id}")
            except Exception as db_error:
                # Non-blocking: ChromaDB storage succeeded, PostgreSQL update failed
                # This is acceptable for batch processing where records may not exist in DB
                self.logger.warning(
                    f"PostgreSQL update failed for memory_log {memory_log_id}: {db_error}. "
                    f"Vector storage in ChromaDB succeeded."
                )

            self.logger.info(
                f"Vector stored: {memory_id} for memory_log {memory_log_id}"
            )

        except Exception as e:
            self.logger.error(
                f"Failed to store vector for memory_log {event_data.get('memory_log_id')}: {e}"
            )
            # Non-blocking failure - memory log already exists in PostgreSQL
