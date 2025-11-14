"""
Temporal Decay Reranking

Single Responsibility: Apply exponential temporal decay to search results.

This module implements exponential decay reranking to boost recent memories
while gracefully degrading older memories based on configurable half-life.
"""

from typing import List
from datetime import datetime
from src.infrastructure.chromadb.models import SearchResult


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
