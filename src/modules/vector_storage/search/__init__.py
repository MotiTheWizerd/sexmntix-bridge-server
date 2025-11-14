"""
Search Module

Handles semantic search and result filtering operations.
"""

from src.modules.vector_storage.search.similarity_search_handler import SimilaritySearchHandler
from src.modules.vector_storage.search.similarity_filter import SimilarityFilter
from src.modules.vector_storage.search.filters import (
    FilterOrchestrator,
    filter_by_minimum_similarity,
    filter_by_similarity_range,
    get_top_results,
    apply_temporal_decay,
)

__all__ = [
    # Main classes
    "SimilaritySearchHandler",
    "SimilarityFilter",  # Backward compatibility
    # New interfaces
    "FilterOrchestrator",
    # Individual filter functions for direct usage
    "filter_by_minimum_similarity",
    "filter_by_similarity_range",
    "get_top_results",
    "apply_temporal_decay",
]
