"""
Monitoring API Routes

Combines all monitoring-related routers into a single router.
Maintains backward compatibility with original /monitoring prefix.
"""

from fastapi import APIRouter

from . import metrics_routes
from . import health_routes
from . import viewer_routes
from . import search_routes

# Create combined router with /monitoring prefix
router = APIRouter(prefix="/monitoring", tags=["monitoring"])

# Include all sub-routers
router.include_router(metrics_routes.router)
router.include_router(health_routes.router)
router.include_router(viewer_routes.router)
router.include_router(search_routes.router)

__all__ = ["router"]
