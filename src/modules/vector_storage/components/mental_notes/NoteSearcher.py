"""
Note search component for vector storage operations.
"""
from typing import List, Dict, Any, Optional
from src.modules.core import EventBus, Logger
from src.modules.embeddings import EmbeddingService
from src.infrastructure.chromadb.repository import VectorRepository
from src.modules.vector_storage.search import SimilarityFilter


class NoteSearcher:
    """
    Component responsible for searching mental notes in vector storage.
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

    async def search_mental_notes(
        self,
        query: str,
        user_id: str,
        project_id: str,
        limit: int = 10,
        session_id: Optional[str] = None,
        note_type: Optional[str] = None,
        min_similarity: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Semantic search for mental notes.

        Args:
            query: Search query text
            user_id: User identifier for collection isolation
            project_id: Project identifier for collection isolation
            limit: Maximum number of results
            session_id: Optional filter by session ID
            note_type: Optional filter by note type (observation, decision, etc.)
            min_similarity: Minimum similarity threshold (0.0 to 1.0)

        Returns:
            List of search results with similarity scores
        """
        # Generate embedding for query
        embedding_result = await self.embedding_service.generate_embedding(query)
        query_embedding = embedding_result.embedding

        # Build where filter for mental notes
        where_filter = {"document_type": "mental_note"}

        if session_id:
            where_filter["session_id"] = session_id

        if note_type:
            where_filter["note_type"] = note_type

        # Perform semantic search
        results = await self.vector_repository.search(
            query_embedding=query_embedding,
            user_id=user_id,
            project_id=project_id,
            limit=limit,
            where_filter=where_filter
        )

        # Apply similarity filtering
        filtered_results = self.similarity_filter.apply_filter(
            results,
            min_similarity
        )

        # Publish event
        await self.event_bus.emit("mental_note_search_performed", {
            "query": query,
            "user_id": user_id,
            "project_id": project_id,
            "result_count": len(filtered_results)
        })

        return filtered_results