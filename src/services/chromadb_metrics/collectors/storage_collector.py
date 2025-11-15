"""
Storage metrics collector

Gathers storage health metrics including disk usage and vector storage efficiency.
"""

import os
import shutil
from typing import Dict, Any

from src.modules.core import Logger
from src.infrastructure.chromadb.client import ChromaDBClient
from ..collectors.collection_collector import CollectionMetricsCollector
from ..config import MetricsConfig


class StorageMetricsCollector:
    """Collects storage health metrics"""

    def __init__(
        self,
        chromadb_client: ChromaDBClient,
        collection_collector: CollectionMetricsCollector,
        logger: Logger
    ):
        """Initialize storage metrics collector

        Args:
            chromadb_client: ChromaDB client instance
            collection_collector: Collection metrics collector for total vectors
            logger: Logger instance
        """
        self.chromadb_client = chromadb_client
        self.collection_collector = collection_collector
        self.logger = logger

    async def get_storage_metrics(self) -> Dict[str, Any]:
        """Get storage health metrics

        Returns:
            Dictionary with storage size, disk usage, and health status
        """
        try:
            base_path = self.chromadb_client.base_storage_path

            # Calculate total storage size
            total_size = self._calculate_directory_size(base_path)
            total_mb = total_size / (1024 * 1024)

            # Get disk usage
            disk_usage = self._get_disk_usage(base_path)
            disk_total_gb = disk_usage.total / (1024**3)
            disk_free_gb = disk_usage.free / (1024**3)
            disk_used_gb = (disk_usage.total - disk_usage.free) / (1024**3)

            # Calculate average bytes per vector
            collection_metrics = await self.collection_collector.get_collection_metrics()
            total_vectors = collection_metrics.get("total_vectors", 0)
            avg_bytes_per_vector = total_size / total_vectors if total_vectors > 0 else 0

            # Storage health status
            utilization = (total_mb / (disk_total_gb * 1024)) * 100 if disk_total_gb > 0 else 0
            health_status = self._determine_health_status(utilization)

            return {
                "total_storage_mb": round(total_mb, 2),
                "disk_total_gb": round(disk_total_gb, 2),
                "disk_free_gb": round(disk_free_gb, 2),
                "disk_used_gb": round(disk_used_gb, 2),
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
                "health_status": MetricsConfig.HEALTH_UNKNOWN,
            }

    def _calculate_directory_size(self, path: str) -> int:
        """Calculate total size of a directory

        Args:
            path: Directory path

        Returns:
            Total size in bytes
        """
        total_size = 0
        if os.path.exists(path):
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(filepath)
                    except OSError:
                        pass
        return total_size

    def _get_disk_usage(self, path: str):
        """Get disk usage statistics

        Args:
            path: Path to check disk usage for

        Returns:
            Disk usage statistics object
        """
        check_path = path if os.path.exists(path) else "."
        return shutil.disk_usage(check_path)

    def _determine_health_status(self, utilization: float) -> str:
        """Determine storage health status based on utilization

        Args:
            utilization: Storage utilization percentage

        Returns:
            Health status string
        """
        if utilization > MetricsConfig.STORAGE_CRITICAL_THRESHOLD:
            return MetricsConfig.HEALTH_CRITICAL
        elif utilization > MetricsConfig.STORAGE_WARNING_THRESHOLD:
            return MetricsConfig.HEALTH_WARNING
        else:
            return MetricsConfig.HEALTH_HEALTHY
