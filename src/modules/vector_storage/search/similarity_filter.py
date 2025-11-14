"""
Similarity Filter (Backward Compatibility Wrapper)

Single Responsibility: Maintain backward compatibility with existing code.

This module acts as a compatibility facade, delegating all calls to the new
FilterOrchestrator. Existing code using SimilarityFilter continues to work
without any changes.

Note: New code should use FilterOrchestrator or individual filter functions
from the filters/ module for clearer semantics and better composability.
"""

from typing import List
from src.infrastructure.chromadb.models import SearchResult
from .filters import FilterOrchestrator


class SimilarityFilter:
    """
    Filters search results based on similarity thresholds.

    DEPRECATED: Use FilterOrchestrator or individual filter functions instead.
    This class is maintained for backward compatibility.

    Provides reusable filtering strategies for semantic search results.
    """

    @staticmethod
    def filter_by_minimum_similarity(
        results: List[SearchResult],
        min_similarity: float = 0.0
    ) -> List[SearchResult]:
        """
        Filter results by minimum similarity threshold.

        Args:
            results: List of search results
            min_similarity: Minimum similarity threshold (0.0 to 1.0)

        Returns:
            Filtered list of search results
        """
        return FilterOrchestrator.filter_by_minimum_similarity(
            results, min_similarity
        )

    @staticmethod
    def filter_by_similarity_range(
        results: List[SearchResult],
        min_similarity: float = 0.0,
        max_similarity: float = 1.0
    ) -> List[SearchResult]:
        """
        Filter results by similarity range.

        Args:
            results: List of search results
            min_similarity: Minimum similarity threshold (0.0 to 1.0)
            max_similarity: Maximum similarity threshold (0.0 to 1.0)

        Returns:
            Filtered list of search results
        """
        return FilterOrchestrator.filter_by_similarity_range(
            results, min_similarity, max_similarity
        )

    @staticmethod
    def get_top_results(
        results: List[SearchResult],
        limit: int
    ) -> List[SearchResult]:
        """
        Get top N results by similarity score.

        Results are assumed to be pre-sorted by similarity (highest first).

        Args:
            results: List of search results
            limit: Maximum number of results to return

        Returns:
            Top N search results
        """
        return FilterOrchestrator.get_top_results(results, limit)

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
        return FilterOrchestrator.filter_and_limit(
            results, min_similarity, limit
        )

    @staticmethod
    def apply_temporal_decay(
        results: List[SearchResult],
        enable_temporal_decay: bool = False,
        half_life_days: float = 30.0
    ) -> List[SearchResult]:
        """
        Apply exponential temporal decay to rerank search results.

        Recent memories are boosted while older memories gracefully decay
        using an exponential decay formula with configurable half-life.

        Formula: final_score = similarity × (0.5 ^ (age_in_days / half_life_days))

        Examples with half_life=30 days:
        - 15 days old: retains 84% of original score
        - 30 days old: retains 50% of original score
        - 60 days old: retains 25% of original score
        - 90 days old: retains 12.5% of original score

        Args:
            results: List of search results
            enable_temporal_decay: Enable temporal decay reranking (default: False)
            half_life_days: Half-life in days for exponential decay (default: 30)

        Returns:
            Reranked list of search results sorted by decayed similarity
        """
        return FilterOrchestrator.apply_temporal_decay(
            results, enable_temporal_decay, half_life_days
        )
