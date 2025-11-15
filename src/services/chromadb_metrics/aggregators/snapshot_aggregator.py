"""
Snapshot Aggregator

Aggregates all metrics into a complete snapshot.
"""

from typing import Dict, Any
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.core import Logger
from src.services.chromadb_metrics.core.event_store import EventStore
from src.services.chromadb_metrics.collectors import (
    CollectionMetricsCollector,
    IngestionMetricsCollector,
    SearchPerformanceCollector,
    SearchQualityCollector,
    StorageMetricsCollector,
)


class SnapshotAggregator:
    """Aggregates all metrics into a complete snapshot."""

    def __init__(
        self,
        collection_collector: CollectionMetricsCollector,
        ingestion_collector: IngestionMetricsCollector,
        search_perf_collector: SearchPerformanceCollector,
        search_quality_collector: SearchQualityCollector,
        storage_collector: StorageMetricsCollector,
        event_store: EventStore,
        logger: Logger
    ):
        """
        Initialize aggregator.

        Args:
            collection_collector: Collection metrics collector
            ingestion_collector: Ingestion metrics collector
            search_perf_collector: Search performance collector
            search_quality_collector: Search quality collector
            storage_collector: Storage metrics collector
            event_store: Event store with metrics
            logger: Logger instance
        """
        self.collection_collector = collection_collector
        self.ingestion_collector = ingestion_collector
        self.search_perf_collector = search_perf_collector
        self.search_quality_collector = search_quality_collector
        self.storage_collector = storage_collector
        self.event_store = event_store
        self.logger = logger

    async def aggregate(self, db_session: AsyncSession) -> Dict[str, Any]:
        """
        Get complete metrics snapshot for UI.

        Args:
            db_session: Database session

        Returns:
            Complete metrics snapshot
        """
        try:
            collection_metrics = await self.collection_collector.collect()
            ingestion_metrics = await self.ingestion_collector.collect(db_session)
            search_performance = await self.search_perf_collector.collect()
            search_quality = await self.search_quality_collector.collect()
            storage_metrics = await self.storage_collector.collect()

            return {
                "timestamp": datetime.utcnow().isoformat(),
                "collections": collection_metrics,
                "ingestion": ingestion_metrics,
                "search_performance": search_performance,
                "search_quality": search_quality,
                "storage": storage_metrics,
                "counters": self.event_store.get_all_counters(),
            }
        except Exception as e:
            self.logger.error(f"Error getting metrics snapshot: {e}", exc_info=True)
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
            }
