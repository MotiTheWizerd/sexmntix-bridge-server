from fastapi import APIRouter, Depends
from src.modules.core import EventBus, Logger
from src.api.dependencies.event_bus import get_event_bus
from src.api.dependencies.logger import get_logger

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check(
    event_bus: EventBus = Depends(get_event_bus),
    logger: Logger = Depends(get_logger)
):
    logger.info("Health check requested")
    event_bus.publish("health_check", {"status": "healthy"})
    return {"status": "healthy"}
