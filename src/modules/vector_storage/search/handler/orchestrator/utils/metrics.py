"""
Metrics Utilities for Search Operations

Utilities for collecting and calculating search metrics.
"""

from typing import Dict, Any, List
from src.infrastructure.chromadb.repository import VectorRepository


async def get_collection_size(
    vector_repository: VectorRepository,
    user_id: str,
    project_id: str
) -> int:
    """
    Get the size of a collection.

    Args:
        vector_repository: Vector repository instance
        user_id: User identifier
        project_id: Project identifier

    Returns:
        Number of items in collection
    """
    return await vector_repository.count(user_id, project_id)


def calculate_result_statistics(results: List[Any]) -> Dict[str, Any]:
    """
    Calculate statistics from search results.

    Args:
        results: List of search results

    Returns:
        Dictionary with statistics
    """
    if not results:
        return {
            "count": 0,
            "avg_similarity": 0.0,
            "max_similarity": 0.0,
            "min_similarity": 0.0
        }

    similarities = [r.similarity for r in results if hasattr(r, 'similarity')]

    if not similarities:
        return {
            "count": len(results),
            "avg_similarity": 0.0,
            "max_similarity": 0.0,
            "min_similarity": 0.0
        }

    return {
        "count": len(results),
        "avg_similarity": sum(similarities) / len(similarities),
        "max_similarity": max(similarities),
        "min_similarity": min(similarities)
    }


async def collect_search_metrics(
    vector_repository: VectorRepository,
    user_id: str,
    project_id: str,
    results: List[Any],
    duration_seconds: float
) -> Dict[str, Any]:
    """
    Collect comprehensive search metrics.

    Args:
        vector_repository: Vector repository instance
        user_id: User identifier
        project_id: Project identifier
        results: Search results
        duration_seconds: Search duration in seconds

    Returns:
        Dictionary with all metrics
    """
    collection_size = await get_collection_size(vector_repository, user_id, project_id)
    result_stats = calculate_result_statistics(results)

    return {
        "duration_seconds": duration_seconds,
        "duration_ms": duration_seconds * 1000,
        "collection_size": collection_size,
        **result_stats
    }
