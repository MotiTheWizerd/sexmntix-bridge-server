"""
Filters Module

Provides filtering, ranking, and reranking strategies for search results.
Includes both individual filter functions and a high-level FilterOrchestrator.
"""

from typing import List
from src.infrastructure.chromadb.models import SearchResult
from .similarity_filters import (
    filter_by_minimum_similarity,
    filter_by_similarity_range,
)
from .ranking import get_top_results
from .temporal_decay import apply_temporal_decay


class FilterOrchestrator:
    """
    Orchestrates filtering, ranking, and reranking of search results.

    Provides a high-level interface to combine filtering strategies
    in a composable way.
    """

    @staticmethod
    def filter_by_minimum_similarity(
        results: List[SearchResult],
        min_similarity: float = 0.0
    ) -> List[SearchResult]:
        """Filter results by minimum similarity threshold."""
        return filter_by_minimum_similarity(results, min_similarity)

    @staticmethod
    def filter_by_similarity_range(
        results: List[SearchResult],
        min_similarity: float = 0.0,
        max_similarity: float = 1.0
    ) -> List[SearchResult]:
        """Filter results by similarity range."""
        return filter_by_similarity_range(results, min_similarity, max_similarity)

    @staticmethod
    def get_top_results(
        results: List[SearchResult],
        limit: int
    ) -> List[SearchResult]:
        """Get top N results by similarity score."""
        return get_top_results(results, limit)

    @staticmethod
    def apply_temporal_decay(
        results: List[SearchResult],
        enable_temporal_decay: bool = False,
        half_life_days: float = 30.0
    ) -> List[SearchResult]:
        """Apply exponential temporal decay to results."""
        return apply_temporal_decay(results, enable_temporal_decay, half_life_days)

    @staticmethod
    def filter_and_limit(
        results: List[SearchResult],
        min_similarity: float = 0.0,
        limit: int = 10
    ) -> List[SearchResult]:
        """
        Filter by minimum similarity and limit results.

        Combines filtering and limiting in a single operation.

        Args:
            results: List of search results
            min_similarity: Minimum similarity threshold (0.0 to 1.0)
            limit: Maximum number of results to return

        Returns:
            Filtered and limited search results
        """
        filtered = filter_by_minimum_similarity(results, min_similarity)
        return get_top_results(filtered, limit)

    @staticmethod
    def filter_and_apply_decay(
        results: List[SearchResult],
        min_similarity: float = 0.0,
        limit: int = 10,
        enable_temporal_decay: bool = False,
        half_life_days: float = 30.0
    ) -> List[SearchResult]:
        """
        Filter, limit, and apply temporal decay to results.

        Combines all filtering strategies in one operation.

        Args:
            results: List of search results
            min_similarity: Minimum similarity threshold (0.0 to 1.0)
            limit: Maximum number of results to return
            enable_temporal_decay: Enable temporal decay reranking
            half_life_days: Half-life in days for exponential decay

        Returns:
            Processed and reranked search results
        """
        # First filter by minimum similarity
        filtered = filter_by_minimum_similarity(results, min_similarity)

        # Apply temporal decay if enabled
        if enable_temporal_decay:
            decayed = apply_temporal_decay(
                filtered,
                enable_temporal_decay=True,
                half_life_days=half_life_days
            )
            # Re-limit after decay since re-sorting might have changed top results
            return get_top_results(decayed, limit)
        else:
            # Just limit if decay is disabled
            return get_top_results(filtered, limit)


__all__ = [
    # Orchestrator/Facade
    "FilterOrchestrator",
    # Individual filters for direct usage
    "filter_by_minimum_similarity",
    "filter_by_similarity_range",
    "get_top_results",
    "apply_temporal_decay",
]
