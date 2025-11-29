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
        memory_log: Dict[str, Any],
        user_id: str,
        project_id: str
    ) -> Tuple[str, List[float]]:
        """
        Store memory log vector in ChromaDB.

        Args:
            memory_log_id: Memory log ID from PostgreSQL
            memory_log: Raw memory log data
            user_id: User identifier
            project_id: Project identifier

        Returns:
            Tuple of (memory_id from ChromaDB, embedding vector)
        """
        vector_service = self.create_vector_service(user_id, project_id)

        memory_id, embedding = await vector_service.store_memory_vector(
            memory_log_id=memory_log_id,
            memory_data=memory_log,
            user_id=user_id,
            project_id=project_id
        )

        return memory_id, embedding

    async def store_mental_note_vector(
        self,
        mental_note_id: int,
        content: str,
        user_id: str,
        project_id: str
    ) -> Tuple[str, List[float]]:
        """
        Store mental note vector in ChromaDB.

        Args:
            mental_note_id: Mental note ID from PostgreSQL
            content: Mental note content text
            user_id: User identifier
            project_id: Project identifier

        Returns:
            Tuple of (note_id from ChromaDB, embedding vector)
        """
        vector_service = self.create_vector_service(user_id, project_id)

        note_id, embedding = await vector_service.store_mental_note_vector(
            mental_note_id=mental_note_id,
            mental_note_data=content,
            user_id=user_id,
            project_id=project_id
        )

        return note_id, embedding

    async def store_conversation_vector(
        self,
        conversation_db_id: int,
        memory_log: Dict[str, Any],
        user_id: str,
        project_id: str,
        session_id: str = None,
        gemini_analysis: List[Dict[str, Any]] = None
    ) -> Tuple[List[str], List[List[float]]]:
        """
        Store conversation memory units in separate ChromaDB collection.

        Storage structure: user_id/conversations/{conversation_id}/
        Note: project_id is NOT used for conversations (user-scoped only)

        Args:
            conversation_db_id: Conversation ID from PostgreSQL
            memory_log: Raw conversation data (for metadata only)
            user_id: User identifier
            session_id: Optional session identifier for grouping conversations
            gemini_analysis: List of Gemini-enriched memory units

        Returns:
            Tuple of (list of conversation_ids, list of embedding vectors)
        """
        vector_service = self.create_vector_service(user_id, project_id)

        conversation_ids, embeddings = await vector_service.store_conversation_vector(
            conversation_db_id=conversation_db_id,
            conversation_data=memory_log,
            user_id=user_id,
            project_id=project_id,
            session_id=session_id,
            gemini_analysis=gemini_analysis
        )

        return conversation_ids, embeddings
