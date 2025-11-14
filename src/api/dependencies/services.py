"""
Dependency injection for application services.
"""

from fastapi import Request
from src.services.chromadb_metrics_service import ChromaDBMetricsCollector


def get_chromadb_metrics_collector(request: Request) -> ChromaDBMetricsCollector:
    """
    Get the ChromaDB metrics collector instance from application state.

    Args:
        request: FastAPI request object

    Returns:
        ChromaDBMetricsCollector instance
    """
    return request.app.state.chromadb_metrics_collector
