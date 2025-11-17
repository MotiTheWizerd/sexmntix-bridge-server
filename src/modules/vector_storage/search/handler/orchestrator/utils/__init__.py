"""
Search Workflow Utilities

Helper functions for timing and metrics collection.
"""

from .timing import (
    start_timer,
    calculate_duration,
    calculate_duration_ms,
    format_duration_ms,
)

from .metrics import (
    get_collection_size,
    calculate_result_statistics,
    collect_search_metrics,
)

__all__ = [
    # Timing
    "start_timer",
    "calculate_duration",
    "calculate_duration_ms",
    "format_duration_ms",
    # Metrics
    "get_collection_size",
    "calculate_result_statistics",
    "collect_search_metrics",
]
