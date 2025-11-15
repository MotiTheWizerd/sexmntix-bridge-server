"""
ChromaDB Metrics Service

Provides comprehensive metrics collection for ChromaDB operations.
"""

from .service import ChromaDBMetricsCollector
from .models import MetricEvent
from .collectors import (
    CollectionMetricsCollector,
    IngestionMetricsCollector,
    SearchPerformanceCollector,
    SearchQualityCollector,
    StorageMetricsCollector,
)
from .calculators import PercentileCalculator, RateCalculator
from .aggregators import SnapshotAggregator

__all__ = [
    # Main service (for backward compatibility and standard usage)
    "ChromaDBMetricsCollector",

    # Models
    "MetricEvent",

    # Collectors (for advanced/specialized usage)
    "CollectionMetricsCollector",
    "IngestionMetricsCollector",
    "SearchPerformanceCollector",
    "SearchQualityCollector",
    "StorageMetricsCollector",

    # Utilities (for custom implementations)
    "PercentileCalculator",
    "RateCalculator",
    "SnapshotAggregator",
]
