"""
ChromaDB Metrics Collector Service (Orchestrator)

Main service that orchestrates all metric collection components
and maintains backward compatibility with the original API.
"""

from typing import Dict, List, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.services.base_service import BaseService
from src.modules.core import EventBus, Logger
from src.infrastructure.chromadb.client import ChromaDBClient
from src.services.chromadb_metrics.core.event_store import EventStore
from src.services.chromadb_metrics.core.event_handlers import EventHandlers
from src.services.chromadb_metrics.calculators import PercentileCalculator, RateCalculator
from src.services.chromadb_metrics.collectors import (
    CollectionMetricsCollector,
    IngestionMetricsCollector,
    SearchPerformanceCollector,
    SearchQualityCollector,
    StorageMetricsCollector,
)
from src.services.chromadb_metrics.aggregators import SnapshotAggregator


class ChromaDBMetricsCollector(BaseService):
    """
    Orchestrates metric collection via specialized collectors.

    Maintains backward compatibility with original API while delegating
    to focused, single-responsibility components.

    Features:
    - Real-time metric collection via EventBus
    - In-memory storage for recent events (last 1000)
    - Statistical aggregation (percentiles, averages)
    - Time-series data for dashboards
    """

    def __init__(
        self,
        event_bus: EventBus,
        logger: Logger,
        chromadb_client: ChromaDBClient,
        max_events: int = 1000
    ):
        """
        Initialize metrics collector.

        Args:
            event_bus: EventBus for subscribing to events
            logger: Logger instance
            chromadb_client: ChromaDB client
            max_events: Maximum events to keep in memory
        """
        super().__init__(event_bus, logger)
        self.chromadb_client = chromadb_client

        # Core components
        self.event_store = EventStore(max_events)
        self.event_handlers = EventHandlers(event_bus, self.event_store, logger)

        # Calculators
        self.percentile_calc = PercentileCalculator()
        self.rate_calc = RateCalculator()

        # Collectors
        self.collection_collector = CollectionMetricsCollector(chromadb_client, logger)
        self.ingestion_collector = IngestionMetricsCollector(logger)
        self.search_perf_collector = SearchPerformanceCollector(
            self.event_store, self.percentile_calc, self.rate_calc, logger
        )
        self.search_quality_collector = SearchQualityCollector(self.event_store, logger)
        self.storage_collector = StorageMetricsCollector(
            chromadb_client, self.collection_collector, logger
        )

        # Aggregator
        self.snapshot_aggregator = SnapshotAggregator(
            collection_collector=self.collection_collector,
            ingestion_collector=self.ingestion_collector,
            search_perf_collector=self.search_perf_collector,
            search_quality_collector=self.search_quality_collector,
            storage_collector=self.storage_collector,
            event_store=self.event_store,
            logger=logger,
        )

        self.logger.info("ChromaDBMetricsCollector initialized")

    # ========== Backward-compatible API (delegating to components) ==========

    def record_event(
        self,
        metric_type: str,
        value: float,
        tags: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record a metric event."""
        self.event_store.record_event(metric_type, value, tags)

    def get_percentile(self, metric: str, percentile: int) -> float:
        """Calculate percentile for a timer metric."""
        values = self.event_store.get_timer_values(metric)
        return self.percentile_calc.calculate(values, percentile)

    def get_rate(self, metric: str, window_seconds: int = 60) -> float:
        """Calculate rate (events per second) over time window."""
        events = self.event_store.get_events(metric)
        return self.rate_calc.calculate(events, window_seconds)

    async def get_collection_metrics(self) -> Dict[str, Any]:
        """Get metrics about ChromaDB collections."""
        return await self.collection_collector.collect()

    async def get_ingestion_metrics(self, db_session: AsyncSession) -> Dict[str, Any]:
        """Get vector ingestion metrics from database."""
        return await self.ingestion_collector.collect(db_session)

    async def get_search_performance_metrics(self) -> Dict[str, Any]:
        """Get search performance metrics."""
        return await self.search_perf_collector.collect()

    async def get_search_quality_metrics(self) -> Dict[str, Any]:
        """Get search quality metrics."""
        return await self.search_quality_collector.collect()

    async def get_storage_metrics(self) -> Dict[str, Any]:
        """Get storage health metrics."""
        return await self.storage_collector.collect()

    async def get_snapshot(self, db_session: AsyncSession) -> Dict[str, Any]:
        """Get complete metrics snapshot for UI."""
        return await self.snapshot_aggregator.aggregate(db_session)
