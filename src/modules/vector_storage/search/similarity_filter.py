"""
Similarity Filter

Single Responsibility: Filter search results based on similarity thresholds.

This component applies similarity-based filtering to search results,
ensuring only results meeting minimum similarity requirements are returned.
"""

from typing import List
from datetime import datetime
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
        # If temporal decay is disabled, return results unchanged
        if not enable_temporal_decay:
            return results

        # If no results or invalid half-life, return unchanged
        if not results or half_life_days <= 0:
            return results

        # Get current timestamp for age calculation
        current_timestamp = datetime.utcnow().timestamp()

        # Apply temporal decay to each result
        for result in results:
            # Get memory timestamp from metadata
            memory_timestamp = result.metadata.get("date")

            # Skip if no date metadata available
            if memory_timestamp is None:
                continue

            # Calculate age in days
            age_seconds = current_timestamp - memory_timestamp
            age_days = age_seconds / 86400  # Convert seconds to days

            # Ensure age is non-negative (handle future dates gracefully)
            if age_days < 0:
                age_days = 0

            # Calculate exponential decay factor: 0.5 ^ (age_in_days / half_life_days)
            decay_factor = 0.5 ** (age_days / half_life_days)

            # Apply decay to similarity score
            original_similarity = result.similarity
            result.similarity = original_similarity * decay_factor

            # Store original similarity in metadata for debugging/transparency
            if not hasattr(result, 'original_similarity'):
                result.original_similarity = original_similarity
            result.decay_factor = decay_factor
            result.age_days = age_days

        # Re-sort results by decayed similarity (descending)
        sorted_results = sorted(
            results,
            key=lambda r: r.similarity,
            reverse=True
        )

        return sorted_results
