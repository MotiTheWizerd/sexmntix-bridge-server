"""
Vector storage orchestration for internal handlers.

Coordinates VectorStorageService creation and vector storage operations
for memory logs and mental notes.
"""

from typing import Dict, Any, Tuple, List
from src.modules.core import EventBus, Logger
from src.modules.embeddings import EmbeddingService
from src.api.dependencies.vector_storage import create_vector_storage_service


class VectorStorageOrchestrator:
    """Orchestrates vector storage operations"""

    def __init__(
        self,
        embedding_service: EmbeddingService,
        event_bus: EventBus,
        logger: Logger
    ):
        """
        Initialize vector storage orchestrator.

        Args:
            embedding_service: Service for generating embeddings
            event_bus: Event bus for publishing events
            logger: Logger instance
        """
        self.embedding_service = embedding_service
        self.event_bus = event_bus
        self.logger = logger

    def create_vector_service(self, user_id: str, project_id: str):
        """
        Create VectorStorageService for specific user/project.

        Args:
            user_id: User identifier
            project_id: Project identifier

        Returns:
            VectorStorageService instance
        """
        return create_vector_storage_service(
            user_id=user_id,
            project_id=project_id,
            embedding_service=self.embedding_service,
            event_bus=self.event_bus,
            logger=self.logger
        )

    async def store_memory_vector(
        self,
        memory_log_id: int,
        raw_data: Dict[str, Any],
        user_id: str,
        project_id: str
    ) -> Tuple[str, List[float]]:
        """
        Store memory log vector in ChromaDB.

        Args:
            memory_log_id: Memory log ID from PostgreSQL
            raw_data: Raw memory log data
            user_id: User identifier
            project_id: Project identifier

        Returns:
            Tuple of (memory_id from ChromaDB, embedding vector)
        """
        vector_service = self.create_vector_service(user_id, project_id)

        memory_id, embedding = await vector_service.store_memory_vector(
            memory_log_id=memory_log_id,
            memory_data=raw_data,
            user_id=user_id,
            project_id=project_id
        )

        return memory_id, embedding

    async def store_mental_note_vector(
        self,
        mental_note_id: int,
        raw_data: Dict[str, Any],
        user_id: str,
        project_id: str
    ) -> Tuple[str, List[float]]:
        """
        Store mental note vector in ChromaDB.

        Args:
            mental_note_id: Mental note ID from PostgreSQL
            raw_data: Raw mental note data
            user_id: User identifier
            project_id: Project identifier

        Returns:
            Tuple of (note_id from ChromaDB, embedding vector)
        """
        vector_service = self.create_vector_service(user_id, project_id)

        note_id, embedding = await vector_service.store_mental_note_vector(
            mental_note_id=mental_note_id,
            mental_note_data=raw_data,
            user_id=user_id,
            project_id=project_id
        )

        return note_id, embedding
