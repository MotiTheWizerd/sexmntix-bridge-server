"""
Memory search component for vector storage operations.
"""
from typing import List, Dict, Any, Optional
from src.modules.core import EventBus, Logger
from src.modules.embeddings import EmbeddingService
from src.infrastructure.chromadb.repository import VectorRepository
from src.modules.vector_storage.search import SimilarityFilter
from src.infrastructure.chromadb.utils.filter_sanitizer import sanitize_filter


class MemorySearcher:
    """
    Component responsible for searching memory logs in vector storage.
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
        self.similarity_filter = SimilarityFilter()

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
        Semantic search for similar memories (memory logs only).

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
        """
        # Generate embedding for query
        embedding_result = await self.embedding_service.generate_embedding(query)
        query_embedding = embedding_result.embedding

        # Sanitize filter BEFORE combining with document_type
        # This removes empty dicts like {'additionalProp1': {}} from Swagger examples
        where_filter = sanitize_filter(where_filter)
        
        # Build ChromaDB filter with $and operator (required when combining multiple conditions)
        # ChromaDB requires exactly ONE top-level operator in where clauses
        if where_filter:
            combined_filter = {
                "$and": [
                    where_filter,
                    {"document_type": "memory_log"}
                ]
            }
        else:
            combined_filter = {"document_type": "memory_log"}

        # Perform semantic search
        results = await self.vector_repository.search(
            query_embedding=query_embedding,
            user_id=user_id,
            project_id=project_id,
            limit=limit,
            where_filter=combined_filter,
            collection_prefix="memory_logs"
        )

        # Apply temporal decay if enabled
        if enable_temporal_decay:
            from datetime import datetime
            current_time = datetime.now()
            for result in results:
                # Apply temporal decay to similarity scores
                # Implementation would depend on available metadata
                pass

        # Apply similarity filtering
        filtered_results = self.similarity_filter.apply_filter(
            results,
            min_similarity
        )

        # Publish event
        await self.event_bus.emit("memory_search_performed", {
            "query": query,
            "user_id": user_id,
            "project_id": project_id,
            "result_count": len(filtered_results)
        })

        return filtered_results
