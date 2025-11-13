"""
Similarity Filter

Single Responsibility: Filter search results based on similarity thresholds.

This component applies similarity-based filtering to search results,
ensuring only results meeting minimum similarity requirements are returned.
"""

from typing import List
from src.infrastructure.chromadb.repository import SearchResult


class SimilarityFilter:
    """
    Filters search results based on similarity thresholds.

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
        return [
            result for result in results
            if result.similarity >= min_similarity
        ]

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
        return [
            result for result in results
            if min_similarity <= result.similarity <= max_similarity
        ]

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
        return results[:limit]

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
        filtered = SimilarityFilter.filter_by_minimum_similarity(
            results, min_similarity
        )
        return SimilarityFilter.get_top_results(filtered, limit)
