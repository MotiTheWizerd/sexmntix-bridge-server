"""
Memory storage component for vector storage operations.
"""
from typing import List, Dict, Any, Optional, Tuple
from src.modules.core import EventBus, Logger
from src.modules.embeddings import EmbeddingService
from src.infrastructure.chromadb.repository import VectorRepository
from src.modules.vector_storage.text_extraction import MemoryTextExtractor


class MemoryStorer:
    """
    Component responsible for storing memory logs in vector storage.
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
        self.text_extractor = MemoryTextExtractor(logger)

    async def store_memory_vector(
        self,
        memory_log_id: int,
        memory_data: Dict[str, Any],
        user_id: str,
        project_id: str,
        text_override: Optional[str] = None
    ) -> Tuple[str, List[float]]:
        """
        Generate embedding and store memory in ChromaDB.

        Args:
            memory_log_id: Database ID of memory log
            memory_data: Complete memory log data
            user_id: User identifier for collection isolation
            project_id: Project identifier for collection isolation
            text_override: Optional text to embed (overrides extraction)

        Returns:
            Tuple of (memory_id, embedding_vector)
        """
        # Extract searchable text using TextExtractor
        if text_override:
            searchable_text = text_override
        else:
            searchable_text = self.text_extractor.extract_with_fallback(
                memory_data=memory_data,
                memory_log_id=memory_log_id
            )

        # Generate embedding from text
        embedding_result = await self.embedding_service.generate_embedding(searchable_text)
        embedding = embedding_result.embedding

        # Convert raw data to the format expected by add_memory
        memory_log_data = {
            "raw_data": memory_data,
            "content": searchable_text,
            "metadata": {
                "document_type": "memory_log",
                "memory_log_id": memory_log_id,
                **memory_data.get("metadata", {})
            }
        }

        # Store in vector repository
        memory_id = await self.vector_repository.add_memory(
            memory_log_id=memory_log_id,
            embedding=embedding,
            memory_data=memory_log_data,
            user_id=user_id,
            project_id=project_id
        )

        # Publish event
        await self.event_bus.emit("memory_vector_stored", {
            "memory_id": memory_id,
            "memory_log_id": memory_log_id,
            "user_id": user_id,
            "project_id": project_id
        })

        return memory_id, embedding