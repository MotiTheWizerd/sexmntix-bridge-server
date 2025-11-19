"""
Memory retrieval component for vector storage operations.
"""
from typing import List, Dict, Any, Optional
from src.modules.core import EventBus, Logger
from src.modules.embeddings import EmbeddingService
from src.infrastructure.chromadb.repository import VectorRepository


class MemoryRetriever:
    """
    Component responsible for retrieving, deleting, and counting memories in vector storage.
    """
    def __init__(
        self,
        event_bus: EventBus,
        logger: Logger,
        embedding_service: EmbeddingService,
        vector_repository: VectorRepository
    ):
        self.event_bus = event_bus
        self.logger = logger
        self.embedding_service = embedding_service
        self.vector_repository = vector_repository

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
        try:
            result = await self.vector_repository.get_by_id(
                memory_id=memory_id,
                user_id=user_id,
                project_id=project_id
            )
            
            if result:
                # Publish event
                await self.event_bus.emit("memory_retrieved", {
                    "memory_id": memory_id,
                    "user_id": user_id,
                    "project_id": project_id
                })
            
            return result
        except Exception:
            return None

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
        success = await self.vector_repository.delete(
            memory_id=memory_id,
            user_id=user_id,
            project_id=project_id
        )
        
        if success:
            # Publish event
            await self.event_bus.emit("memory_deleted", {
                "memory_id": memory_id,
                "user_id": user_id,
                "project_id": project_id
            })
        
        return success

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
        count = await self.vector_repository.count(
            user_id=user_id,
            project_id=project_id
        )
        
        # Publish event
        await self.event_bus.emit("memory_count_retrieved", {
            "user_id": user_id,
            "project_id": project_id,
            "count": count
        })
        
        return count