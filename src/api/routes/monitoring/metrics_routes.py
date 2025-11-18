"""
Monitoring Metrics API Routes

Provides endpoints for ChromaDB metrics collection.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any

from src.api.dependencies.database import get_db_session
from src.api.dependencies.services import get_chromadb_metrics_collector
from src.services.chromadb_metrics import ChromaDBMetricsCollector
from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter()


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
