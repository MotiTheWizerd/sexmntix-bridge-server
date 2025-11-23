"""
Dependency injection factories for memory logs routes.

Provides FastAPI dependencies for creating services with proper context.
"""
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.dependencies.database import get_db_session
from src.api.dependencies.event_bus import get_event_bus
from src.api.dependencies.logger import get_logger
from src.api.dependencies.vector_storage import create_vector_storage_service
from src.database.repositories.memory_log_repository import MemoryLogRepository
from src.services.memory_log_service import MemoryLogService
from src.modules.core import EventBus, Logger
from src.modules.vector_storage import VectorStorageService


async def get_memory_log_repository(
    db: AsyncSession = Depends(get_db_session)
) -> MemoryLogRepository:
    """
    Create memory log repository instance.

    Args:
        db: Database session

    Returns:
        MemoryLogRepository instance
    """
    return MemoryLogRepository(db)


async def get_memory_log_service(
    repository: MemoryLogRepository = Depends(get_memory_log_repository),
    event_bus: EventBus = Depends(get_event_bus),
    logger: Logger = Depends(get_logger)
) -> MemoryLogService:
    """
    Create memory log service for non-search operations.

    Args:
        repository: Memory log repository
        event_bus: Event bus for async operations
        logger: Logger instance

    Returns:
        MemoryLogService instance (without vector service)
    """
    return MemoryLogService(
        repository=repository,
        vector_service=None,
        event_bus=event_bus,
        logger=logger
    )


async def get_vector_service_for_user(
    user_id: str,
    project_id: str,
    request: Request,
    logger: Logger = Depends(get_logger)
) -> VectorStorageService:
    """
    Create vector storage service for specific user/project.

    Args:
        user_id: User identifier
        project_id: Project identifier
        request: FastAPI request (for app.state access)
        logger: Logger instance

    Returns:
        VectorStorageService instance
    """
    return create_vector_storage_service(
        user_id=user_id,
        project_id=project_id,
        embedding_service=request.app.state.embedding_service,
        event_bus=request.app.state.event_bus,
        logger=logger
    )


async def get_search_service(
    user_id: str,
    project_id: str,
    request: Request,
    logger: Logger = Depends(get_logger)
) -> MemoryLogService:
    """
    Create memory log service with vector search capability.

    Args:
        user_id: User identifier
        project_id: Project identifier
        request: FastAPI request (for app.state access)
        logger: Logger instance

    Returns:
        MemoryLogService instance with vector service
    """
    vector_service = await get_vector_service_for_user(
        user_id=user_id,
        project_id=project_id,
        request=request,
        logger=logger
    )

    return MemoryLogService(
        repository=None,
        vector_service=vector_service,
        event_bus=None,
        logger=logger
    )
