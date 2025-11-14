"""
Monitoring API Routes

Provides endpoints for system monitoring and metrics:
- /monitoring/chromadb - ChromaDB metrics
- /monitoring/health/detailed - Comprehensive health check
- /monitoring/metrics - Overall system metrics
"""

from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from typing import Dict, Any

from src.api.dependencies.database import get_db_session
from src.api.dependencies.services import get_chromadb_metrics_collector
from src.services.chromadb_metrics_service import ChromaDBMetricsCollector
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/chromadb")
async def get_chromadb_metrics(
    db_session: AsyncSession = Depends(get_db_session),
    metrics_collector: ChromaDBMetricsCollector = Depends(get_chromadb_metrics_collector),
) -> Dict[str, Any]:
    """
    Get comprehensive ChromaDB metrics.

    Returns:
        - Collections: count, sizes, vectors
        - Ingestion: daily/weekly/monthly stats, timeline
        - Search Performance: latency percentiles, rates
        - Search Quality: similarity scores, result distribution
        - Storage: disk usage, health status
    """
    try:
        snapshot = await metrics_collector.get_snapshot(db_session)
        return snapshot
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting ChromaDB metrics: {str(e)}")


@router.get("/chromadb/collections")
async def get_collection_metrics(
    metrics_collector: ChromaDBMetricsCollector = Depends(get_chromadb_metrics_collector),
) -> Dict[str, Any]:
    """Get detailed collection metrics"""
    try:
        return await metrics_collector.get_collection_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting collection metrics: {str(e)}")


@router.get("/chromadb/ingestion")
async def get_ingestion_metrics(
    db_session: AsyncSession = Depends(get_db_session),
    metrics_collector: ChromaDBMetricsCollector = Depends(get_chromadb_metrics_collector),
) -> Dict[str, Any]:
    """Get vector ingestion metrics with time-series data"""
    try:
        return await metrics_collector.get_ingestion_metrics(db_session)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting ingestion metrics: {str(e)}")


@router.get("/chromadb/search-performance")
async def get_search_performance_metrics(
    metrics_collector: ChromaDBMetricsCollector = Depends(get_chromadb_metrics_collector),
) -> Dict[str, Any]:
    """Get search performance metrics (latency, throughput)"""
    try:
        return await metrics_collector.get_search_performance_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting search performance metrics: {str(e)}")


@router.get("/chromadb/search-quality")
async def get_search_quality_metrics(
    metrics_collector: ChromaDBMetricsCollector = Depends(get_chromadb_metrics_collector),
) -> Dict[str, Any]:
    """Get search quality metrics (similarity scores, result distribution)"""
    try:
        return await metrics_collector.get_search_quality_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting search quality metrics: {str(e)}")


@router.get("/chromadb/storage")
async def get_storage_metrics(
    metrics_collector: ChromaDBMetricsCollector = Depends(get_chromadb_metrics_collector),
) -> Dict[str, Any]:
    """Get storage health metrics"""
    try:
        return await metrics_collector.get_storage_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting storage metrics: {str(e)}")


@router.get("/health/detailed")
async def detailed_health_check(
    db_session: AsyncSession = Depends(get_db_session),
    metrics_collector: ChromaDBMetricsCollector = Depends(get_chromadb_metrics_collector),
) -> Dict[str, Any]:
    """
    Comprehensive health check including all subsystems.

    Returns health status for:
    - Database connection
    - ChromaDB
    - Storage
    - Overall metrics
    """
    checks = {
        "timestamp": datetime.utcnow().isoformat(),
        "status": "healthy",
        "checks": {}
    }

    # Database check
    try:
        result = await db_session.execute("SELECT 1")
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

    # ChromaDB check
    try:
        collection_metrics = await metrics_collector.get_collection_metrics()
        if "error" in collection_metrics:
            checks["checks"]["chromadb"] = {
                "status": "unhealthy",
                "message": collection_metrics["error"]
            }
            checks["status"] = "degraded"
        else:
            checks["checks"]["chromadb"] = {
                "status": "healthy",
                "message": f"{collection_metrics['total_collections']} collections, {collection_metrics['total_vectors']} vectors",
                "collections": collection_metrics["total_collections"],
                "vectors": collection_metrics["total_vectors"]
            }
    except Exception as e:
        checks["checks"]["chromadb"] = {
            "status": "unhealthy",
            "message": f"ChromaDB error: {str(e)}"
        }
        checks["status"] = "degraded"

    # Storage check
    try:
        storage_metrics = await metrics_collector.get_storage_metrics()
        if "error" in storage_metrics:
            checks["checks"]["storage"] = {
                "status": "warning",
                "message": storage_metrics["error"]
            }
        else:
            storage_status = storage_metrics.get("health_status", "unknown")
            checks["checks"]["storage"] = {
                "status": storage_status,
                "message": f"{storage_metrics['total_storage_mb']} MB used, {storage_metrics['storage_utilization']}% utilization",
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

    return checks
