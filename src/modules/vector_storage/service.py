"""
Vector Storage Service

Single Responsibility: Orchestrate vector storage operations by delegating
to specialized components.

This service acts as a facade/coordinator, composing:
- MemoryTextExtractor: Extract searchable text from data
- MemoryStorageHandler: Handle vector storage operations
- SimilaritySearchHandler: Handle semantic search operations
"""

from typing import List, Dict, Any, Optional
from src.services.base_service import BaseService
from src.modules.core import EventBus, Logger
from src.modules.embeddings import EmbeddingService
from src.infrastructure.chromadb.repository import VectorRepository

from src.modules.vector_storage.text_extraction import MemoryTextExtractor
from src.modules.vector_storage.storage import MemoryStorageHandler
from src.modules.vector_storage.search import SimilaritySearchHandler, SimilarityFilter


class VectorStorageService(BaseService):
    """
    Service for managing vector embeddings and semantic search.

    Orchestrates specialized components:
    - MemoryTextExtractor: Text extraction from memory data
    - MemoryStorageHandler: Vector storage operations
    - SimilaritySearchHandler: Semantic search operations
    - SimilarityFilter: Result filtering

    Features:
    - Automatic embedding generation from text
    - Dual storage: PostgreSQL + ChromaDB
    - Semantic search with similarity scoring
    - Event-driven architecture
    """

    def __init__(
        self,
        event_bus: EventBus,
        logger: Logger,
        embedding_service: EmbeddingService,
        vector_repository: VectorRepository
    ):
        """
        Initialize vector storage service with component composition.

        Args:
            event_bus: Event bus for publishing domain events
            logger: Logger instance
            embedding_service: Service for generating embeddings
            vector_repository: Repository for ChromaDB operations
        """
        super().__init__(event_bus, logger)

        # Initialize specialized components
        self.text_extractor = MemoryTextExtractor(logger)

        self.storage_handler = MemoryStorageHandler(
            event_bus=event_bus,
            logger=logger,
            embedding_service=embedding_service,
            vector_repository=vector_repository
        )

        self.similarity_filter = SimilarityFilter()

        self.search_handler = SimilaritySearchHandler(
            event_bus=event_bus,
            logger=logger,
            embedding_service=embedding_service,
            vector_repository=vector_repository,
            similarity_filter=self.similarity_filter
        )

        self.logger.info("VectorStorageService initialized with modular components")

    def _register_handlers(self):
        """Register event handlers if needed."""
        pass

    async def store_memory_vector(
        self,
        memory_log_id: int,
        memory_data: Dict[str, Any],
        user_id: str,
        project_id: str,
        text_override: Optional[str] = None
    ) -> tuple[str, List[float]]:
        """
        Generate embedding and store in ChromaDB.

        Delegates to specialized components:
        1. MemoryTextExtractor: Extract searchable text
        2. MemoryStorageHandler: Store vector

        Args:
            memory_log_id: Database ID of memory log
            memory_data: Complete memory log data
            user_id: User identifier for collection isolation
            project_id: Project identifier for collection isolation
            text_override: Optional text to embed (overrides extraction)

        Returns:
            Tuple of (memory_id, embedding_vector)

        Raises:
            InvalidTextError: If searchable text is empty
            ProviderError: If embedding generation fails
        """
        # Extract searchable text using TextExtractor
        if text_override:
            searchable_text = text_override
        else:
            searchable_text = self.text_extractor.extract_with_fallback(
                memory_data=memory_data,
                memory_log_id=memory_log_id
            )

        # Store vector using StorageHandler
        return await self.storage_handler.store_memory_vector(
            memory_log_id=memory_log_id,
            searchable_text=searchable_text,
            memory_data=memory_data,
            user_id=user_id,
            project_id=project_id
        )

    async def search_similar_memories(
        self,
        query: str,
        user_id: str,
        project_id: str,
        limit: int = 10,
        where_filter: Optional[Dict[str, Any]] = None,
        min_similarity: float = 0.0,
        enable_temporal_decay: bool = False,
        half_life_days: float = 30.0
    ) -> List[Dict[str, Any]]:
        """
        Semantic search for similar memories.

        Delegates to SimilaritySearchHandler.

        Args:
            query: Search query text
            user_id: User identifier for collection isolation
            project_id: Project identifier for collection isolation
            limit: Maximum number of results
            where_filter: Optional metadata filter (ChromaDB where syntax)
            min_similarity: Minimum similarity threshold (0.0 to 1.0)
            enable_temporal_decay: Apply exponential decay based on memory age (default: False)
            half_life_days: Half-life in days for exponential decay (default: 30)

        Returns:
            List of search results with similarity scores

        Example:
            results = await service.search_similar_memories(
                query="authentication bug fix",
                user_id="user123",
                project_id="project456",
                limit=5,
                min_similarity=0.5,
                enable_temporal_decay=True,
                half_life_days=30
            )
        """
        return await self.search_handler.search_similar_memories(
            query=query,
            user_id=user_id,
            project_id=project_id,
            limit=limit,
            where_filter=where_filter,
            min_similarity=min_similarity,
            enable_temporal_decay=enable_temporal_decay,
            half_life_days=half_life_days
        )

    async def get_memory(
        self,
        memory_id: str,
        user_id: str,
        project_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve specific memory by ID.

        Delegates to MemoryStorageHandler.

        Args:
            memory_id: Memory identifier
            user_id: User identifier
            project_id: Project identifier

        Returns:
            Memory document dict or None if not found
        """
        return await self.storage_handler.get_memory(
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

        Delegates to MemoryStorageHandler.

        Args:
            memory_id: Memory identifier
            user_id: User identifier
            project_id: Project identifier

        Returns:
            True if deleted, False if not found
        """
        return await self.storage_handler.delete_memory(
            memory_id=memory_id,
            user_id=user_id,
            project_id=project_id
        )

    async def count_memories(
        self,
        user_id: str,
        project_id: str
    ) -> int:
        """
        Count memories in user/project collection.

        Delegates to MemoryStorageHandler.

        Args:
            user_id: User identifier
            project_id: Project identifier

        Returns:
            Number of memories
        """
        return await self.storage_handler.count_memories(
            user_id=user_id,
            project_id=project_id
        )
