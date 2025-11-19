"""
Core service initialization.

Initializes EventBus, Logger, and SocketService.
"""

from src.modules.core import EventBus, Logger
from src.services.socket_service import SocketService


def initialize_core_services() -> tuple[EventBus, Logger, SocketService]:
    """Initialize core application services.

    Creates the fundamental services needed by the application:
    - EventBus for event-driven communication
    - Logger for application logging
    - SocketService for real-time communication

    Returns:
        Tuple of (event_bus, logger, socket_service)
    """
    event_bus = EventBus()
    logger = Logger("semantic-bridge-server")
    socket_service = SocketService(event_bus, logger)

    logger.info("Core services initialized (EventBus, Logger, SocketService)")

    return event_bus, logger, socket_service
