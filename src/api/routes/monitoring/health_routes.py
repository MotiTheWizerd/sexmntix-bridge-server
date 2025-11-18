"""
Health Check API Routes

Provides comprehensive health check endpoints for all subsystems.
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any

from src.api.dependencies.database import get_db_session
from src.api.dependencies.services import get_chromadb_metrics_collector
from src.services.chromadb_metrics import ChromaDBMetricsCollector
from src.services.monitoring import HealthCheckService
from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter()


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
    health_service = HealthCheckService(metrics_collector)
    return await health_service.detailed_health_check(db_session)
