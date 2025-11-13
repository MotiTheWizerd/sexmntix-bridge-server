"""
Dependency injection for event handlers.

Registers internal event handlers on application startup.
"""

from typing import Callable
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.core import EventBus, Logger
from src.events.internal_handlers import MemoryLogStorageHandlers
from src.modules.vector_storage import VectorStorageService


_handlers_initialized = False


def initialize_event_handlers(
    event_bus: EventBus,
    logger: Logger,
    db_session_factory: Callable,
    vector_service: VectorStorageService
):
    """
    Initialize and register all internal event handlers.

    Should be called once during application startup.

    Args:
        event_bus: Application event bus
        logger: Application logger
        db_session_factory: Factory function to create database sessions
        vector_service: Vector storage service instance
    """
    global _handlers_initialized

    if _handlers_initialized:
        logger.info("Event handlers already initialized")
        return

    logger.info("Initializing internal event handlers...")

    # Create handler instance
    handlers = MemoryLogStorageHandlers(
        db_session_factory=db_session_factory,
        vector_service=vector_service,
        logger=logger
    )

    # Register handler for memory_log.stored event (ChromaDB vector storage)
    # This executes as background task after PostgreSQL storage completes
    event_bus.subscribe(
        "memory_log.stored",
        handlers.handle_memory_log_stored
    )

    _handlers_initialized = True
    logger.info("Internal event handlers registered successfully")
