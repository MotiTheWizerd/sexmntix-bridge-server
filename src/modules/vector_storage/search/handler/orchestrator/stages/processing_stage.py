"""
Processing Stage for Search Workflow

Handles result filtering and ranking (temporal decay).
"""

from typing import List
from src.infrastructure.chromadb.models import SearchResult
from ....filters import FilterOrchestrator
from ...models import SearchRequest
from ...telemetry import SearchTelemetry


class ProcessingStage:
    """
    Stage 3: Filter and rank search results.

    Responsibilities:
    - Filter by minimum similarity threshold
    - Apply temporal decay reranking (if enabled)
    - Log processing operations with telemetry
    """

    def __init__(self, telemetry: SearchTelemetry):
        """
        Initialize the processing stage.

        Args:
            telemetry: Telemetry handler for logging
        """
        self.telemetry = telemetry

    def execute(
        self,
        results: List[SearchResult],
        request: SearchRequest
    ) -> List[SearchResult]:
        """
        Filter and rank search results.

        Applies:
        1. Minimum similarity filtering
        2. Temporal decay reranking (if enabled)

        Args:
            results: Raw search results
            request: The search request

        Returns:
            Processed search results
        """
        # Filter by minimum similarity
        filtered_results = FilterOrchestrator.filter_by_minimum_similarity(
            results=results,
            min_similarity=request.min_similarity
        )

        # Apply temporal decay reranking (if enabled)
        reranked_results = FilterOrchestrator.apply_temporal_decay(
            results=filtered_results,
            enable_temporal_decay=request.enable_temporal_decay,
            half_life_days=request.half_life_days
        )

        # Log temporal decay application
        self.telemetry.log_temporal_decay(
            request.enable_temporal_decay,
            request.half_life_days
        )

        return reranked_results
