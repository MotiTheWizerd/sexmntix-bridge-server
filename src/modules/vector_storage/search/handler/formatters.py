"""
Result Formatters

Single Responsibility: Format search results for different output formats.

This module provides utility functions for converting search results
between different representations (e.g., SearchResult objects to dicts).
"""

from typing import List, Dict, Any
from src.infrastructure.chromadb.models import SearchResult


def format_results_as_dicts(results: List[SearchResult]) -> List[Dict[str, Any]]:
    """
    Convert SearchResult objects to dictionary format.

    This is useful for JSON serialization and API responses.

    Args:
        results: List of SearchResult objects

    Returns:
        List of dictionaries with search result data
    """
    return [result.to_dict() for result in results]


def format_results_summary(
    results: List[Dict[str, Any]],
    query: str,
    duration_ms: float,
    min_similarity: float,
    cached: bool,
    collection_size: int
) -> str:
    """
    Create a human-readable summary of search results.

    Useful for logging and debugging.

    Args:
        results: List of search result dictionaries
        query: The search query
        duration_ms: Search duration in milliseconds
        min_similarity: Minimum similarity threshold used
        cached: Whether the query embedding was cached
        collection_size: Total size of the collection

    Returns:
        Formatted summary string
    """
    return (
        f"Found {len(results)} memories in {duration_ms:.2f}ms "
        f"(min_similarity: {min_similarity}, cached: {cached}, "
        f"collection_size: {collection_size})"
    )


def truncate_query_for_logging(query: str, max_length: int = 100) -> str:
    """
    Truncate a query string for logging purposes.

    Args:
        query: The query string to truncate
        max_length: Maximum length (default: 100)

    Returns:
        Truncated query with ellipsis if needed
    """
    if len(query) <= max_length:
        return query
    return query[:max_length] + "..."
