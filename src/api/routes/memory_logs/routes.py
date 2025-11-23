"""
Memory logs API routes - Thin orchestration layer.

Routes delegate to handlers for business logic orchestration.
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from src.api.dependencies.database import get_db_session
from src.api.dependencies.logger import get_logger
from src.api.schemas.memory_log import (
    MemoryLogResponse,
    MemoryLogSearchRequest,
    MemoryLogSearchResult,
    MemoryLogDateSearchRequest,
)
from src.api.routes.memory_logs.handlers import (
    CreateMemoryLogHandler,
    GetMemoryLogHandler,
    ListMemoryLogsHandler,
    SearchMemoryLogHandler,
    DateSearchMemoryLogHandler,
)
from src.api.routes.memory_logs.dependencies import (
    get_memory_log_repository,
    get_memory_log_service,
)
from src.database.repositories.memory_log_repository import MemoryLogRepository
from src.services.memory_log_service import MemoryLogService
from src.modules.core import Logger
from src.api.dependencies.vector_storage import create_vector_storage_service

router = APIRouter(prefix="/memory-logs", tags=["memory-logs"])


@router.post("", response_model=MemoryLogResponse, status_code=201)
async def create_memory_log(
    request: Request,
    service: MemoryLogService = Depends(get_memory_log_service),
    logger: Logger = Depends(get_logger),
):
    """
    Create a new memory log with automatic embedding generation via event-driven architecture.

    New Comprehensive Format:
    {
        "user_id": "uuid-string",
        "project_id": "default",
        "session_id": "string",
        "task": "task-name-kebab-case",
        "agent": "claude-sonnet-4",
        "memory_log": {
            "component": "component-name",
            "complexity": {...},
            "outcomes": {...},
            "solution": {...},
            "gotchas": [...],
            "code_context": {...},
            "future_planning": {...},
            "user_context": {...},
            "semantic_context": {...},
            "tags": ["searchable", "keywords"],
            ... (all other fields optional)
        }
    }

    Hybrid Event-Driven Workflow:
    1. Store memory log in PostgreSQL (synchronous for immediate persistence)
    2. Emit memory_log.stored event with memory_log_id
    3. ChromaDB handler generates embedding and stores vector (async background task)

    This approach ensures data integrity while enabling async vector storage
    for better performance and non-blocking failures.

    User and project IDs enable multi-tenant isolation in vector storage.
    The system automatically adds a datetime field and calculates temporal_context if not provided.
    """
    return await CreateMemoryLogHandler.handle(request, service, logger)


@router.get("/{id}", response_model=MemoryLogResponse)
async def get_memory_log(
    id: str,
    repository: MemoryLogRepository = Depends(get_memory_log_repository),
    logger: Logger = Depends(get_logger),
):
    """Fetch a memory log by ID."""
    return await GetMemoryLogHandler.handle(id, repository, logger)


@router.get("", response_model=List[MemoryLogResponse])
async def list_memory_logs(
    limit: int = 100,
    repository: MemoryLogRepository = Depends(get_memory_log_repository),
    logger: Logger = Depends(get_logger),
):
    """List memory logs with optional limit."""
    return await ListMemoryLogsHandler.handle(limit, repository, logger)


@router.post("/search")
async def search_memory_logs(
    search_request: MemoryLogSearchRequest,
    request: Request,
    format: str = "text",
    logger: Logger = Depends(get_logger),
):
    """
    Semantic search for memory logs by meaning, not keywords.

    Uses vector embeddings to find similar memories based on semantic similarity.
    Each user/project gets their own isolated ChromaDB database.

    Example:
        POST /memory-logs/search?format=json
        {
            "query": "authentication bug fix",
            "user_id": "user123",
            "project_id": "project456",
            "limit": 5,
            "min_similarity": 0.5,
            "filters": {
                "component": "auth-module",
                "date": {"$gte": "2025-11-01"}
            }
        }

    Returns memories ranked by similarity with scores.
    Format parameter: 'json' for structured data, 'text' for terminal output.
    """
    # Create vector service for this user/project
    vector_service = create_vector_storage_service(
        user_id=search_request.user_id,
        project_id=search_request.project_id,
        embedding_service=request.app.state.embedding_service,
        event_bus=request.app.state.event_bus,
        logger=logger
    )

    # Create service with vector capability
    service = MemoryLogService(None, vector_service, None, logger)

    return await SearchMemoryLogHandler.handle(
        search_request, service, format, logger
    )


@router.post("/search-by-date")
async def search_memory_logs_by_date(
    search_request: MemoryLogDateSearchRequest,
    request: Request,
    format: str = "text",
    logger: Logger = Depends(get_logger),
):
    """
    Search memory logs with date filtering.

    Supports both explicit date ranges and convenience time period shortcuts:
    - recent: Last 7 days
    - last-week: Last 7 days
    - last-month: Last 30 days
    - archived: Older than 30 days

    Example:
        POST /memory-logs/search-by-date?format=json
        {
            "query": "authentication bug fix",
            "user_id": "user123",
            "project_id": "project456",
            "limit": 10,
            "time_period": "recent"
        }

        OR with explicit dates:
        {
            "query": "authentication bug fix",
            "user_id": "user123",
            "project_id": "project456",
            "start_date": "2024-01-01T00:00:00",
            "end_date": "2024-12-31T23:59:59"
        }

    Format parameter: 'json' for structured data, 'text' for terminal output.
    """
    # Create vector service for this user/project
    vector_service = create_vector_storage_service(
        user_id=search_request.user_id,
        project_id=search_request.project_id,
        embedding_service=request.app.state.embedding_service,
        event_bus=request.app.state.event_bus,
        logger=logger
    )

    # Create service with vector capability
    service = MemoryLogService(None, vector_service, None, logger)

    return await DateSearchMemoryLogHandler.handle(
        search_request, service, format, logger
    )
