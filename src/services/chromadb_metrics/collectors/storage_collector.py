"""
Storage Metrics Collector

Collects disk storage and health metrics.
"""

import os
import shutil
from typing import Dict, Any

from src.infrastructure.chromadb.client import ChromaDBClient
from src.modules.core import Logger
from src.services.chromadb_metrics.collectors.collection_collector import CollectionMetricsCollector


class StorageMetricsCollector:
    """Collects storage and disk health metrics."""

    def __init__(
        self,
        chromadb_client: ChromaDBClient,
        collection_collector: CollectionMetricsCollector,
        logger: Logger
    ):
        """
        Initialize collector.

        Args:
            chromadb_client: ChromaDB client instance
            collection_collector: Collection metrics collector
            logger: Logger instance
        """
        self.chromadb_client = chromadb_client
        self.collection_collector = collection_collector
        self.logger = logger

    async def collect(self) -> Dict[str, Any]:
        """
        Get storage health metrics.

        Returns:
            Dictionary with storage metrics
        """
        try:
            base_path = self.chromadb_client.base_storage_path

            # Calculate total storage size
            total_size = 0
            if os.path.exists(base_path):
                for dirpath, dirnames, filenames in os.walk(base_path):
                    for filename in filenames:
                        filepath = os.path.join(dirpath, filename)
                        try:
                            total_size += os.path.getsize(filepath)
                        except OSError:
                            pass

            total_mb = total_size / (1024 * 1024)

            # Get disk usage
            disk_usage = shutil.disk_usage(base_path if os.path.exists(base_path) else ".")
            disk_total_gb = disk_usage.total / (1024**3)
            disk_free_gb = disk_usage.free / (1024**3)

            # Calculate average bytes per vector
            collection_metrics = await self.collection_collector.collect()
            total_vectors = collection_metrics.get("total_vectors", 0)
            avg_bytes_per_vector = total_size / total_vectors if total_vectors > 0 else 0

            # Storage health status
            utilization = (total_mb / (disk_total_gb * 1024)) * 100 if disk_total_gb > 0 else 0

            if utilization > 90:
                health_status = "critical"
            elif utilization > 75:
                health_status = "warning"
            else:
                health_status = "healthy"

            return {
                "total_storage_mb": round(total_mb, 2),
                "disk_total_gb": round(disk_total_gb, 2),
                "disk_free_gb": round(disk_free_gb, 2),
                "disk_used_gb": round((disk_total_gb - disk_free_gb), 2),
                "storage_utilization": round(utilization, 2),
                "avg_bytes_per_vector": round(avg_bytes_per_vector, 2),
                "total_vectors": total_vectors,
                "health_status": health_status,
            }
        except Exception as e:
            self.logger.error(f"Error getting storage metrics: {e}", exc_info=True)
            return {
                "total_storage_mb": 0,
                "error": str(e),
                "health_status": "unknown",
            }
