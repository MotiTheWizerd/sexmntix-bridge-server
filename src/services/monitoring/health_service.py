"""
Health Check Service

Orchestrates health checks across multiple subsystems.
Extracts health check logic from route handlers.
"""

from datetime import datetime
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.chromadb_metrics import ChromaDBMetricsCollector


class HealthCheckService:
    """Service for performing system health checks"""

    def __init__(self, metrics_collector: ChromaDBMetricsCollector):
        self.metrics_collector = metrics_collector

    async def detailed_health_check(
        self,
        db_session: AsyncSession
    ) -> Dict[str, Any]:
        """
        Comprehensive health check including all subsystems.

        Args:
            db_session: Database session for health checks

        Returns:
            Health status for database, ChromaDB, storage, and overall system
        """
        checks = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "healthy",
            "checks": {}
        }

        # Perform all health checks
        await self._check_database_health(db_session, checks)
        await self._check_chromadb_health(checks)
        await self._check_storage_health(checks)

        return checks

    async def _check_database_health(
        self,
        db_session: AsyncSession,
        checks: Dict[str, Any]
    ) -> None:
        """Check database connectivity"""
        try:
            await db_session.execute("SELECT 1")
            checks["checks"]["database"] = {
                "status": "healthy",
                "message": "Database connection successful"
            }
        except Exception as e:
            checks["checks"]["database"] = {
                "status": "unhealthy",
                "message": f"Database error: {str(e)}"
            }
            checks["status"] = "degraded"

    async def _check_chromadb_health(
        self,
        checks: Dict[str, Any]
    ) -> None:
        """Check ChromaDB status"""
        try:
            collection_metrics = await self.metrics_collector.get_collection_metrics()

            if "error" in collection_metrics:
                checks["checks"]["chromadb"] = {
                    "status": "unhealthy",
                    "message": collection_metrics["error"]
                }
                checks["status"] = "degraded"
            else:
                checks["checks"]["chromadb"] = {
                    "status": "healthy",
                    "message": (
                        f"{collection_metrics['total_collections']} collections, "
                        f"{collection_metrics['total_vectors']} vectors"
                    ),
                    "collections": collection_metrics["total_collections"],
                    "vectors": collection_metrics["total_vectors"]
                }
        except Exception as e:
            checks["checks"]["chromadb"] = {
                "status": "unhealthy",
                "message": f"ChromaDB error: {str(e)}"
            }
            checks["status"] = "degraded"

    async def _check_storage_health(
        self,
        checks: Dict[str, Any]
    ) -> None:
        """Check storage health"""
        try:
            storage_metrics = await self.metrics_collector.get_storage_metrics()

            if "error" in storage_metrics:
                checks["checks"]["storage"] = {
                    "status": "warning",
                    "message": storage_metrics["error"]
                }
            else:
                storage_status = storage_metrics.get("health_status", "unknown")
                checks["checks"]["storage"] = {
                    "status": storage_status,
                    "message": (
                        f"{storage_metrics['total_storage_mb']} MB used, "
                        f"{storage_metrics['storage_utilization']}% utilization"
                    ),
                    "disk_free_gb": storage_metrics.get("disk_free_gb", 0),
                    "utilization": storage_metrics.get("storage_utilization", 0)
                }

                if storage_status in ["warning", "critical"]:
                    checks["status"] = "degraded"

        except Exception as e:
            checks["checks"]["storage"] = {
                "status": "warning",
                "message": f"Storage check error: {str(e)}"
            }
