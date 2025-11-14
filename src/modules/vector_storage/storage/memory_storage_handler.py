"""
Memory Storage Handler

Single Responsibility: Handle memory vector storage operations.

This component orchestrates the workflow of:
1. Generating embeddings for text
2. Storing vectors in ChromaDB
3. Publishing storage events
"""

from typing import Dict, Any, Optional, List
from src.modules.core import EventBus, Logger
from src.modules.embeddings import EmbeddingService
from src.infrastructure.chromadb.repository import VectorRepository


class MemoryStorageHandler:
    """
    Handles memory vector storage operations.

    Orchestrates:
    - Embedding generation via EmbeddingService
    - Vector storage via VectorRepository
    - Event publishing for storage completion
    """

    def __init__(
        self,
        event_bus: EventBus,
        logger: Logger,
        embedding_service: EmbeddingService,
        vector_repository: VectorRepository
    ):
        """
        Initialize the storage handler.

        Args:
            event_bus: Event bus for publishing events
            logger: Logger instance
            embedding_service: Service for generating embeddings
            vector_repository: Repository for ChromaDB operations
        """
        self.event_bus = event_bus
        self.logger = logger
        self.embedding_service = embedding_service
        self.vector_repository = vector_repository

    async def store_memory_vector(
        self,
        memory_log_id: int,
        searchable_text: str,
        memory_data: Dict[str, Any],
        user_id: str,
        project_id: str
    ) -> tuple[str, List[float]]:
        """
        Generate embedding and store in ChromaDB.

        Workflow:
        1. Generate embedding via EmbeddingService
        2. Store vector in ChromaDB via VectorRepository
        3. Publish storage event

        Args:
            memory_log_id: Database ID of memory log
            searchable_text: Text to embed
            memory_data: Complete memory log data
            user_id: User identifier for collection isolation
            project_id: Project identifier for collection isolation

        Returns:
            Tuple of (memory_id, embedding_vector)

        Raises:
            InvalidTextError: If searchable text is empty
            ProviderError: If embedding generation fails
        """
        text_preview = searchable_text[:100] if searchable_text else "EMPTY"
        self.logger.info(
            f"[STORAGE_HANDLER] Generating embedding for memory_log {memory_log_id} "
            f"(user: {user_id}, project: {project_id})"
        )
        self.logger.info(
            f"[STORAGE_HANDLER] Searchable text - length: {len(searchable_text)}, preview: {text_preview}"
        )

        # Generate embedding
        try:
            embedding_response = await self.embedding_service.generate_embedding(
                text=searchable_text
            )
            self.logger.info(
                f"[STORAGE_HANDLER] Embedding generated successfully - "
                f"dimensions: {len(embedding_response.embedding)}, cached: {embedding_response.cached}"
            )
        except Exception as e:
            self.logger.error(
                f"[STORAGE_HANDLER] Embedding generation failed for memory_log {memory_log_id}: {e}"
            )
            raise

        embedding = embedding_response.embedding

        # Store in ChromaDB
        self.logger.info(f"[STORAGE_HANDLER] Storing vector in ChromaDB...")
        memory_id = await self.vector_repository.add_memory(
            memory_log_id=memory_log_id,
            embedding=embedding,
            memory_data=memory_data,
            user_id=user_id,
            project_id=project_id
        )
        self.logger.info(f"[STORAGE_HANDLER] Vector stored successfully with memory_id: {memory_id}")

        # Publish event
        self.event_bus.publish("vector.stored", {
            "memory_id": memory_id,
            "memory_log_id": memory_log_id,
            "user_id": user_id,
            "project_id": project_id,
            "embedding_dim": len(embedding),
            "cached": embedding_response.cached
        })

        self.logger.info(
            f"[STORAGE_HANDLER] Complete - Vector stored: {memory_id} "
            f"(dim: {len(embedding)}, cached: {embedding_response.cached})"
        )

        return memory_id, embedding

    async def get_memory(
        self,
        memory_id: str,
        user_id: str,
        project_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve specific memory by ID.

        Args:
            memory_id: Memory identifier
            user_id: User identifier
            project_id: Project identifier

        Returns:
            Memory document dict or None if not found
        """
        return await self.vector_repository.get_by_id(
            memory_id=memory_id,
            user_id=user_id,
            project_id=project_id
        )

    async def delete_memory(
        self,
        memory_id: str,
        user_id: str,
        project_id: str
    ) -> bool:
        """
        Delete memory from ChromaDB.

        Args:
            memory_id: Memory identifier
            user_id: User identifier
            project_id: Project identifier

        Returns:
            True if deleted, False if not found
        """
        deleted = await self.vector_repository.delete(
            memory_id=memory_id,
            user_id=user_id,
            project_id=project_id
        )

        if deleted:
            self.event_bus.publish("vector.deleted", {
                "memory_id": memory_id,
                "user_id": user_id,
                "project_id": project_id
            })

        return deleted

    async def count_memories(
        self,
        user_id: str,
        project_id: str
    ) -> int:
        """
        Count memories in user/project collection.

        Args:
            user_id: User identifier
            project_id: Project identifier

        Returns:
            Number of memories
        """
        return await self.vector_repository.count(user_id, project_id)
