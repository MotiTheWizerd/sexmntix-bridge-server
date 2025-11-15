"""
Configuration and constants for ChromaDB metrics collection

Defines thresholds, limits, and metric categorization constants.
"""


class MetricsConfig:
    """Configuration constants for metrics collection"""

    # Event storage limits
    DEFAULT_MAX_EVENTS = 1000

    # Performance thresholds
    SLOW_SEARCH_THRESHOLD_MS = 500

    # Similarity score thresholds for categorization
    SIMILARITY_HIGH_THRESHOLD = 0.8
    SIMILARITY_MEDIUM_THRESHOLD = 0.5
    SIMILARITY_LOW_THRESHOLD = 0.3

    # Storage health thresholds (percentage)
    STORAGE_CRITICAL_THRESHOLD = 90
    STORAGE_WARNING_THRESHOLD = 75

    # Event type names
    EVENT_VECTOR_STORED = "vector.stored"
    EVENT_VECTOR_SEARCHED = "vector.searched"
    EVENT_SEARCH_COMPLETED = "search.completed"
    EVENT_CHROMADB_ERROR = "chromadb.error"

    # Counter names
    COUNTER_VECTORS_STORED = "vectors_stored_total"
    COUNTER_SEARCHES_TOTAL = "searches_total"
    COUNTER_SLOW_SEARCHES = "slow_searches"
    COUNTER_NO_RESULTS = "searches_no_results"
    COUNTER_SIMILARITY_HIGH = "similarity_high"
    COUNTER_SIMILARITY_MEDIUM = "similarity_medium"
    COUNTER_SIMILARITY_LOW = "similarity_low"
    COUNTER_SIMILARITY_VERY_LOW = "similarity_very_low"
    COUNTER_ERRORS = "chromadb_errors"

    # Timer names
    TIMER_SEARCH_LATENCY = "search_latency"

    # Time windows (seconds)
    TIME_WINDOW_HOUR = 3600
    TIME_WINDOW_MINUTE = 60

    # Storage health status values
    HEALTH_CRITICAL = "critical"
    HEALTH_WARNING = "warning"
    HEALTH_HEALTHY = "healthy"
    HEALTH_UNKNOWN = "unknown"
