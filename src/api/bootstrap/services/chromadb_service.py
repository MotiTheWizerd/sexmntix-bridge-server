"""
ChromaDB metrics service initialization.

Initializes ChromaDB client and metrics collector.
"""

from src.modules.core import EventBus, Logger
from src.services.chromadb_metrics import ChromaDBMetricsCollector
from src.infrastructure.chromadb.client import ChromaDBClient
from src.api.bootstrap.config import ServiceConfig


def initialize_chromadb_metrics(
    config: ServiceConfig,
    event_bus: EventBus,
    logger: Logger
) -> ChromaDBMetricsCollector:
    """Initialize ChromaDB metrics collector.

    Creates a ChromaDB client and metrics collector for monitoring.

    Args:
        config: Service configuration containing ChromaDB settings
        event_bus: Application event bus
        logger: Application logger

    Returns:
        ChromaDBMetricsCollector instance
    """
    # Create ChromaDB client (base path, no user/project isolation for metrics)
    chromadb_client = ChromaDBClient(
        storage_path=config.chromadb.base_path,
        user_id=None,
        project_id=None
    )

    logger.info(
        f"ChromaDB client initialized at {config.chromadb.base_path} "
        "(no user/project nesting)"
    )

    # Create metrics collector
    chromadb_metrics_collector = ChromaDBMetricsCollector(
        event_bus=event_bus,
        logger=logger,
        chromadb_client=chromadb_client
    )

    logger.info("ChromaDB metrics collector initialized")

    return chromadb_metrics_collector
