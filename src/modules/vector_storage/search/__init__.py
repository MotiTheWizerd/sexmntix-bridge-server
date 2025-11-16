"""
Search Module

Handles semantic search and result filtering operations.

The module is organized into focused sub-packages:
- handler/: Similarity search handler components
- filters/: Result filtering and ranking strategies

For new code, prefer the refactored components:
    from src.modules.vector_storage.search.handler import BaseSearchHandler, SearchRequest, SearchResponse
    from src.modules.vector_storage.search.filters import FilterOrchestrator

For backward compatibility, the old interfaces still work:
    from src.modules.vector_storage.search import SimilaritySearchHandler, SimilarityFilter
"""

# Backward compatibility imports
from src.modules.vector_storage.search.similarity_search_handler import SimilaritySearchHandler
from src.modules.vector_storage.search.similarity_filter import SimilarityFilter

# Filter module imports
from src.modules.vector_storage.search.filters import (
    FilterOrchestrator,
    filter_by_minimum_similarity,
    filter_by_similarity_range,
    get_top_results,
    apply_temporal_decay,
)

# Handler module imports (new refactored components)
from src.modules.vector_storage.search.handler import (
    BaseSearchHandler,
    SearchRequest,
    SearchResponse,
    SearchTelemetry,
    SearchWorkflowOrchestrator,
    format_results_as_dicts,
    format_results_summary,
    truncate_query_for_logging,
)

__all__ = [
    # Backward compatibility (deprecated, use BaseSearchHandler)
    "SimilaritySearchHandler",
    "SimilarityFilter",
    # Handler components (new, recommended)
    "BaseSearchHandler",
    "SearchRequest",
    "SearchResponse",
    "SearchTelemetry",
    "SearchWorkflowOrchestrator",
    # Formatters
    "format_results_as_dicts",
    "format_results_summary",
    "truncate_query_for_logging",
    # Filter components
    "FilterOrchestrator",
    "filter_by_minimum_similarity",
    "filter_by_similarity_range",
    "get_top_results",
    "apply_temporal_decay",
]
