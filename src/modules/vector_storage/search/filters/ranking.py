"""
Ranking and Limiting

Single Responsibility: Limit and rank search results.

This module provides functions for limiting results to top N items
and future extensibility for additional ranking strategies.
"""

from typing import List
from src.infrastructure.chromadb.models import SearchResult


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
