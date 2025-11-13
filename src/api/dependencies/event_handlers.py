"""
Dependency injection for event handlers.

Registers internal event handlers on application startup.
"""

from typing import Callable
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.core import EventBus, Logger
from src.modules.embeddings import EmbeddingService
from src.events.internal_handlers import MemoryLogStorageHandlers


_handlers_initialized = False


def initialize_event_handlers(
    event_bus: EventBus,
    logger: Logger,
    db_session_factory: Callable,
    embedding_service: EmbeddingService
):
    """
    Initialize and register all internal event handlers.

    Should be called once during application startup.

    Args:
        event_bus: Application event bus
        logger: Application logger
        db_session_factory: Factory function to create database sessions
        embedding_service: Embedding service for generating vectors
    """
    global _handlers_initialized

    if _handlers_initialized:
        logger.info("Event handlers already initialized")
        return

    logger.info("Initializing internal event handlers...")

    # Create handler instance with services needed to create VectorStorageService dynamically
    handlers = MemoryLogStorageHandlers(
        db_session_factory=db_session_factory,
        embedding_service=embedding_service,
        event_bus=event_bus,
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
