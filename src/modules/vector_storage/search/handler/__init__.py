"""
Search Handler Module

Provides a refactored, modular approach to similarity search operations.

The handler/ package splits the original SimilaritySearchHandler into
focused, single-responsibility components:

- models.py: Data models (SearchRequest, SearchResponse)
- formatters.py: Result formatting utilities
- telemetry.py: Event publishing and logging
- orchestrator.py: Search workflow orchestration
- base_handler.py: Main handler class (refactored)

For new code, use BaseSearchHandler which provides better separation
of concerns and additional features like SearchResponse metadata.

For backward compatibility, SimilaritySearchHandler continues to work
by re-exporting BaseSearchHandler.
"""

from .models import SearchRequest, SearchResponse
from .formatters import (
    format_results_as_dicts,
    format_results_summary,
    truncate_query_for_logging
)
from .telemetry import SearchTelemetry
from .orchestrator import SearchWorkflowOrchestrator
from .base_handler import BaseSearchHandler

__all__ = [
    # Data models
    "SearchRequest",
    "SearchResponse",
    # Formatters
    "format_results_as_dicts",
    "format_results_summary",
    "truncate_query_for_logging",
    # Components
    "SearchTelemetry",
    "SearchWorkflowOrchestrator",
    # Main handler
    "BaseSearchHandler",
]
