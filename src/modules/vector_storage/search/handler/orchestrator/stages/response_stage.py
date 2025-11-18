"""
Response Stage for Search Workflow

Handles response building with metrics collection.
"""

from typing import List
from src.infrastructure.chromadb.models import SearchResult
from src.infrastructure.chromadb.repository import VectorRepository
from ...models import SearchRequest, SearchResponse
from ...formatters import format_results_as_dicts
from ..utils.metrics import get_collection_size


class ResponseStage:
    """
    Stage 4: Build the final search response with metrics.

    Responsibilities:
    - Format results to dictionary representation
    - Collect performance metrics
    - Build SearchResponse object
    """

    def __init__(self, vector_repository: VectorRepository):
        """
        Initialize the response stage.

        Args:
            vector_repository: Repository for metrics collection
        """
        self.vector_repository = vector_repository

    async def execute(
        self,
        results: List[SearchResult],
        request: SearchRequest,
        duration_ms: float,
        query_cached: bool
    ) -> SearchResponse:
        """
        Build the final search response with metrics.

        Args:
            results: Processed search results
            request: The original search request
            duration_ms: Search duration in milliseconds
            query_cached: Whether the query embedding was cached

        Returns:
            Complete SearchResponse
        """
        # Convert to dict format
        results_data = format_results_as_dicts(results)

        # Collect metrics
        collection_size = await get_collection_size(
            self.vector_repository,
            request.user_id,
            request.project_id
        )

        # Build response
        return SearchResponse.from_search_results(
            results=results_data,
            request=request,
            duration_ms=duration_ms,
            collection_size=collection_size,
            query_cached=query_cached
        )
