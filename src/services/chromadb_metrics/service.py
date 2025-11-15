"""
ChromaDB Metrics Collection Service

Main service that orchestrates metrics collection from multiple specialized collectors.
"""

from datetime import datetime
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.base_service import BaseService
from src.modules.core import EventBus, Logger
from src.infrastructure.chromadb.client import ChromaDBClient

from .config import MetricsConfig
from .collectors.event_collector import EventCollector
from .collectors.collection_collector import CollectionMetricsCollector
from .collectors.ingestion_collector import IngestionMetricsCollector
from .collectors.search_collector import SearchMetricsCollector
from .collectors.storage_collector import StorageMetricsCollector
from .handlers.event_handlers import MetricsEventHandlers


class ChromaDBMetricsCollector(BaseService):
    """
    Collects and aggregates ChromaDB metrics using specialized collectors.

    Features:
    - Real-time metric collection via EventBus
    - In-memory storage for recent events
    - Statistical aggregation (percentiles, averages)
    - Time-series data for dashboards
    - Modular architecture with specialized collectors
    """

    def __init__(
        self,
        event_bus: EventBus,
        logger: Logger,
        chromadb_client: ChromaDBClient,
        max_events: int = MetricsConfig.DEFAULT_MAX_EVENTS
    ):
        """Initialize metrics collection service

        Args:
            event_bus: Event bus for subscribing to events
            logger: Logger instance
            chromadb_client: ChromaDB client for accessing collections
            max_events: Maximum number of events to store
        """
        super().__init__(event_bus, logger)
        self.chromadb_client = chromadb_client

        # Initialize event collector (in-memory storage)
        self.event_collector = EventCollector(max_events=max_events)

        # Initialize specialized collectors
        self.collection_collector = CollectionMetricsCollector(
            chromadb_client=chromadb_client,
            logger=logger
        )

        self.ingestion_collector = IngestionMetricsCollector(logger=logger)

        self.search_collector = SearchMetricsCollector(
            event_collector=self.event_collector
        )

        self.storage_collector = StorageMetricsCollector(
            chromadb_client=chromadb_client,
            collection_collector=self.collection_collector,
            logger=logger
        )

        # Initialize event handlers
        self.event_handlers = MetricsEventHandlers(
            event_bus=event_bus,
            event_collector=self.event_collector,
            logger=logger
        )

        # Register event handlers
        self.event_handlers.register_handlers()

        self.logger.info("ChromaDBMetricsCollector initialized with modular collectors")

    async def get_collection_metrics(self) -> Dict[str, Any]:
        """Get metrics about ChromaDB collections

        Returns:
            Dictionary with collection statistics
        """
        return await self.collection_collector.get_collection_metrics()

    async def get_ingestion_metrics(self, db_session: AsyncSession) -> Dict[str, Any]:
        """Get vector ingestion metrics from database

        Args:
            db_session: Database session

        Returns:
            Dictionary with ingestion statistics
        """
        return await self.ingestion_collector.get_ingestion_metrics(db_session)

    async def get_search_performance_metrics(self) -> Dict[str, Any]:
        """Get search performance metrics

        Returns:
            Dictionary with search latency and performance statistics
        """
        return await self.search_collector.get_search_performance_metrics()

    async def get_search_quality_metrics(self) -> Dict[str, Any]:
        """Get search quality metrics

        Returns:
            Dictionary with search quality and similarity statistics
        """
        return await self.search_collector.get_search_quality_metrics()

    async def get_storage_metrics(self) -> Dict[str, Any]:
        """Get storage health metrics

        Returns:
            Dictionary with storage and disk usage statistics
        """
        return await self.storage_collector.get_storage_metrics()

    async def get_snapshot(self, db_session: AsyncSession) -> Dict[str, Any]:
        """Get complete metrics snapshot for UI

        Args:
            db_session: Database session

        Returns:
            Complete metrics snapshot with all categories
        """
        try:
            collection_metrics = await self.get_collection_metrics()
            ingestion_metrics = await self.get_ingestion_metrics(db_session)
            search_performance = await self.get_search_performance_metrics()
            search_quality = await self.get_search_quality_metrics()
            storage_metrics = await self.get_storage_metrics()

            return {
                "timestamp": datetime.utcnow().isoformat(),
                "collections": collection_metrics,
                "ingestion": ingestion_metrics,
                "search_performance": search_performance,
                "search_quality": search_quality,
                "storage": storage_metrics,
                "counters": self.event_collector.get_all_counters(),
            }
        except Exception as e:
            self.logger.error(f"Error getting metrics snapshot: {e}", exc_info=True)
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
            }
