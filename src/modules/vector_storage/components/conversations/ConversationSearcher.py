"""
Conversation search component for vector storage operations.
"""
from typing import List, Dict, Any, Optional
from src.modules.core import EventBus, Logger
from src.modules.embeddings import EmbeddingService
from src.infrastructure.chromadb.repository import VectorRepository
from src.modules.vector_storage.search import SimilarityFilter


class ConversationSearcher:
    """
    Component responsible for searching conversations in vector storage.
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

    async def search_similar_conversations(
        self,
        query: str,
        user_id: str,
        project_id: str,
        limit: int = 10,
        where_filter: Optional[Dict[str, Any]] = None,
        min_similarity: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Semantic search for conversations in separate ChromaDB collection.

        Args:
            query: Search query text
            user_id: User identifier for collection isolation
            limit: Maximum number of results
            where_filter: Optional metadata filter (ChromaDB where syntax)
            min_similarity: Minimum similarity threshold (0.0 to 1.0)

        Returns:
            List of search results with similarity scores
        """
        self.logger.info(
            f"[CONVERSATION_SEARCH] Searching conversations for query: '{query[:100]}'"
        )

        # Generate embedding for query
        embedding_result = await self.embedding_service.generate_embedding(query)
        query_embedding = embedding_result.embedding

        # Add document_type filter specifically for conversation memory units
        combined_filter = where_filter.copy() if where_filter else {}
        combined_filter["document_type"] = "conversation_memory_unit"

        # Perform semantic search in conversation-specific collection
        results = await self.vector_repository.search(
            query_embedding=query_embedding,
            user_id=user_id,
            project_id=project_id,
            limit=limit,
            where_filter=combined_filter,
            collection_prefix="conversations"
        )

        # Apply similarity filtering
        filtered_results = self.similarity_filter.apply_filter(
            results,
            min_similarity
        )

        self.logger.info(
            f"[CONVERSATION_SEARCH] Found {len(filtered_results)} matching conversations"
        )

        # Publish event
        await self.event_bus.emit("conversation_search_performed", {
            "query": query,
            "user_id": user_id,
            "result_count": len(filtered_results)
        })

        return filtered_results
