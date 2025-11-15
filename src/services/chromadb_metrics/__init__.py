"""
ChromaDB Metrics Package

Provides comprehensive metrics collection for ChromaDB operations.

This package is organized into the following components:
- service: Main service orchestrator (ChromaDBMetricsCollector)
- models: Data models for metrics
- config: Configuration and constants
- collectors: Specialized metric collectors (collection, ingestion, search, storage)
- aggregators: Statistical aggregation functions
- handlers: EventBus event handlers

Usage:
    from src.services.chromadb_metrics import ChromaDBMetricsCollector

    metrics_service = ChromaDBMetricsCollector(
        event_bus, logger, chromadb_client
    )
"""

from .service import ChromaDBMetricsCollector
from .models import MetricEvent
from .config import MetricsConfig

__all__ = [
    "ChromaDBMetricsCollector",
    "MetricEvent",
    "MetricsConfig"
]
