"""
Similarity Search Handler

Single Responsibility: Handle semantic similarity search operations.

This component orchestrates the workflow of:
1. Generating query embeddings
2. Searching ChromaDB for similar vectors
3. Filtering and formatting results
"""

import time
from typing import Dict, Any, Optional, List
from src.modules.core import EventBus, Logger
from src.modules.embeddings import EmbeddingService
from src.infrastructure.chromadb.repository import VectorRepository, SearchResult
from src.modules.vector_storage.search.similarity_filter import SimilarityFilter


class SimilaritySearchHandler:
    """
    Handles semantic similarity search operations.

    Orchestrates:
    - Query embedding generation via EmbeddingService
    - Vector search via VectorRepository
    - Result filtering via SimilarityFilter
    - Event publishing for search operations
    """

    def __init__(
        self,
        event_bus: EventBus,
        logger: Logger,
        embedding_service: EmbeddingService,
        vector_repository: VectorRepository,
        similarity_filter: SimilarityFilter
    ):
        """
        Initialize the search handler.

        Args:
            event_bus: Event bus for publishing events
            logger: Logger instance
            embedding_service: Service for generating embeddings
            vector_repository: Repository for ChromaDB operations
            similarity_filter: Filter for similarity-based filtering
        """
        self.event_bus = event_bus
        self.logger = logger
        self.embedding_service = embedding_service
        self.vector_repository = vector_repository
        self.similarity_filter = similarity_filter

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

        Workflow:
        1. Generate embedding for query text
        2. Search ChromaDB for similar vectors
        3. Filter by minimum similarity threshold
        4. Apply temporal decay reranking (if enabled)
        5. Convert to dict format
        6. Publish search event

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
            results = await handler.search_similar_memories(
                query="authentication bug fix",
                user_id="user123",
                project_id="project456",
                limit=5,
                min_similarity=0.5,
                enable_temporal_decay=True,
                half_life_days=30
            )
        """
        self.logger.info(
            f"Searching memories for query: '{query[:100]}...' "
            f"(user: {user_id}, project: {project_id})"
        )

        # Start timing
        start_time = time.time()

        # Generate query embedding
        embedding_response = await self.embedding_service.generate_embedding(
            text=query
        )

        query_embedding = embedding_response.embedding
        self.logger.info(
            f"Generated query embedding: {len(query_embedding)} dimensions, "
            f"cached: {embedding_response.cached}"
        )

        # Search ChromaDB
        self.logger.info(
            f"Searching ChromaDB for user_id={user_id}, project_id={project_id}, "
            f"limit={limit}, where_filter={where_filter}"
        )
        search_results = await self.vector_repository.search(
            query_embedding=query_embedding,
            user_id=user_id,
            project_id=project_id,
            limit=limit,
            where_filter=where_filter
        )
        self.logger.info(f"ChromaDB returned {len(search_results)} results before filtering")

        # Filter by minimum similarity
        filtered_results = self.similarity_filter.filter_by_minimum_similarity(
            results=search_results,
            min_similarity=min_similarity
        )

        # Apply temporal decay reranking (if enabled)
        reranked_results = self.similarity_filter.apply_temporal_decay(
            results=filtered_results,
            enable_temporal_decay=enable_temporal_decay,
            half_life_days=half_life_days
        )
        self.logger.info(
            f"Temporal decay {'applied' if enable_temporal_decay else 'skipped'} "
            f"(half_life: {half_life_days} days)"
        )

        # Convert to dict format
        results_data = [result.to_dict() for result in reranked_results]

        # Calculate duration and collection size
        duration_ms = (time.time() - start_time) * 1000
        collection_size = await self.vector_repository.count(user_id, project_id)

        # Publish search event with performance metrics
        self.event_bus.publish("vector.searched", {
            "query": query[:100],
            "user_id": user_id,
            "project_id": project_id,
            "results_count": len(results_data),
            "query_cached": embedding_response.cached,
            "temporal_decay_enabled": enable_temporal_decay,
            "half_life_days": half_life_days if enable_temporal_decay else None,
            "duration_ms": duration_ms,
            "collection_size": collection_size,
        })

        # Publish search quality metrics
        self.event_bus.publish("search.completed", {
            "query": query[:100],
            "results": results_data,
            "user_id": user_id,
            "project_id": project_id,
        })

        self.logger.info(
            f"Found {len(results_data)} memories in {duration_ms:.2f}ms "
            f"(min_similarity: {min_similarity}, cached: {embedding_response.cached}, collection_size: {collection_size})"
        )

        return results_data
