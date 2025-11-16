"""
Base Search Handler

Single Responsibility: Provide the main handler interface for similarity search.

This is the refactored version of SimilaritySearchHandler that delegates to
specialized components for orchestration, telemetry, and formatting.
"""

from typing import Dict, Any, Optional, List
from src.modules.core import EventBus, Logger
from src.modules.embeddings import EmbeddingService
from src.infrastructure.chromadb.repository import VectorRepository
from .models import SearchRequest, SearchResponse
from .telemetry import SearchTelemetry
from .orchestrator import SearchWorkflowOrchestrator


class BaseSearchHandler:
    """
    Main handler for semantic similarity search operations.

    This refactored version delegates to specialized components:
    - SearchTelemetry: Handles logging and event publishing
    - SearchWorkflowOrchestrator: Coordinates the search workflow
    - SearchRequest/SearchResponse: Strongly-typed data models

    The handler maintains a clean, focused interface while allowing
    each component to evolve independently.
    """

    def __init__(
        self,
        event_bus: EventBus,
        logger: Logger,
        embedding_service: EmbeddingService,
        vector_repository: VectorRepository,
        similarity_filter: Optional[Any] = None
    ):
        """
        Initialize the search handler.

        Args:
            event_bus: Event bus for publishing events
            logger: Logger instance
            embedding_service: Service for generating embeddings
            vector_repository: Repository for ChromaDB operations
            similarity_filter: (Deprecated) Kept for backward compatibility. No longer used.
        """
        self.event_bus = event_bus
        self.logger = logger
        self.embedding_service = embedding_service
        self.vector_repository = vector_repository
        self.similarity_filter = similarity_filter  # Backward compatibility

        # Initialize specialized components
        self.telemetry = SearchTelemetry(event_bus, logger)
        self.orchestrator = SearchWorkflowOrchestrator(
            embedding_service,
            vector_repository,
            self.telemetry
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

        This is the main public API for similarity search. It maintains
        backward compatibility with the original interface while using
        the refactored internal components.

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
        # Create strongly-typed request
        request = SearchRequest(
            query=query,
            user_id=user_id,
            project_id=project_id,
            limit=limit,
            where_filter=where_filter,
            min_similarity=min_similarity,
            enable_temporal_decay=enable_temporal_decay,
            half_life_days=half_life_days
        )

        # Execute search workflow
        response = await self.orchestrator.execute_search(request)

        # Return results (maintains backward compatibility)
        return response.results

    async def search_with_metadata(
        self,
        query: str,
        user_id: str,
        project_id: str,
        limit: int = 10,
        where_filter: Optional[Dict[str, Any]] = None,
        min_similarity: float = 0.0,
        enable_temporal_decay: bool = False,
        half_life_days: float = 30.0
    ) -> SearchResponse:
        """
        Semantic search with full metadata response.

        This is an enhanced version of search_similar_memories that returns
        a SearchResponse object with additional metadata like performance
        metrics and context information.

        Args:
            query: Search query text
            user_id: User identifier for collection isolation
            project_id: Project identifier for collection isolation
            limit: Maximum number of results
            where_filter: Optional metadata filter (ChromaDB where syntax)
            min_similarity: Minimum similarity threshold (0.0 to 1.0)
            enable_temporal_decay: Apply exponential decay based on memory age
            half_life_days: Half-life in days for exponential decay

        Returns:
            SearchResponse with results and metadata

        Example:
            response = await handler.search_with_metadata(
                query="authentication bug fix",
                user_id="user123",
                project_id="project456",
                limit=5
            )
            print(f"Found {response.results_count} results in {response.duration_ms}ms")
        """
        request = SearchRequest(
            query=query,
            user_id=user_id,
            project_id=project_id,
            limit=limit,
            where_filter=where_filter,
            min_similarity=min_similarity,
            enable_temporal_decay=enable_temporal_decay,
            half_life_days=half_life_days
        )

        return await self.orchestrator.execute_search(request)
