"""
Similarity Threshold Filters

Single Responsibility: Filter search results based on similarity score thresholds.

This module provides filtering functions for semantic search results based on
minimum and range-based similarity thresholds.
"""

from typing import List
from src.infrastructure.chromadb.models import SearchResult


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
        Filtered list of search results meeting minimum threshold
    """
    return [
        result for result in results
        if result.similarity >= min_similarity
    ]


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
        Filtered list of search results within the specified range
    """
    return [
        result for result in results
        if min_similarity <= result.similarity <= max_similarity
    ]
