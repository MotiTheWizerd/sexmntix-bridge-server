from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from src.api.dependencies.database import get_db_session
from src.api.dependencies.event_bus import get_event_bus
from src.api.dependencies.logger import get_logger
from src.api.dependencies.vector_storage import create_vector_storage_service
from src.api.schemas.memory_log import (
    MemoryLogCreate,
    MemoryLogResponse,
    MemoryLogSearchRequest,
    MemoryLogSearchResult,
    MemoryLogDateSearchRequest,
)
from src.api.formatters.memory_log_formatters import MemoryLogFormatter
from src.database.repositories.memory_log_repository import MemoryLogRepository
from src.services.memory_log_service import MemoryLogService
from src.modules.core import EventBus, Logger

router = APIRouter(prefix="/memory-logs", tags=["memory-logs"])


@router.post("", response_model=MemoryLogResponse, status_code=201)
async def create_memory_log(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    event_bus: EventBus = Depends(get_event_bus),
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
    # Get request body
    body = await request.json()

    # Create service instance
    repo = MemoryLogRepository(db)
    service = MemoryLogService(repo, None, event_bus, logger)
    logger.debug(f"[un warpping] ")
    # Unwrap request body (handles MCP-wrapped format)
    data_dict = service.unwrap_request_body(body)

    # Validate with Pydantic
    data = MemoryLogCreate(**data_dict)
    logger.debug(f"[API_VALIDATED] task={data.task}, agent={data.agent}")

    # Convert memory_log to dict, handling nested models
    memory_log_dict = data.memory_log.model_dump(exclude_none=True)

    # Create memory log via service
    memory_log = await service.create_memory_log(
        task=data.task,
        agent=data.agent,
        session_id=data.session_id,
        memory_log=memory_log_dict,
        user_id=str(data.user_id),
        project_id=data.project_id,
    )

    return memory_log


@router.get("/{id}", response_model=MemoryLogResponse)
async def get_memory_log(
    id: str,
    db: AsyncSession = Depends(get_db_session),
    logger: Logger = Depends(get_logger),
):
    logger.info(f"Fetching memory log: {id}")
    
    repo = MemoryLogRepository(db)
    memory_log = await repo.get_by_id(id)
    
    if not memory_log:
        raise HTTPException(status_code=404, detail="Memory log not found")
    
    return memory_log


@router.get("", response_model=List[MemoryLogResponse])
async def list_memory_logs(
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session),
    logger: Logger = Depends(get_logger),
):
    logger.info(f"Listing memory logs (limit: {limit})")

    repo = MemoryLogRepository(db)
    memory_logs = await repo.get_all(limit=limit)

    return memory_logs


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
        POST /memory-logs/search
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
    """
    try:
        # Create VectorStorageService for this specific user/project
        vector_service = create_vector_storage_service(
            user_id=search_request.user_id,
            project_id=search_request.project_id,
            embedding_service=request.app.state.embedding_service,
            event_bus=request.app.state.event_bus,
            logger=logger
        )

        # Create service instance
        service = MemoryLogService(None, vector_service, None, logger)

        # Search via service
        results = await service.search_memory_logs(
            query=search_request.query,
            user_id=search_request.user_id,
            project_id=search_request.project_id,
            limit=search_request.limit,
            filters=search_request.filters,
            tag=search_request.tag,
            min_similarity=search_request.min_similarity
        )

        # Format results using formatter
        search_results = MemoryLogFormatter.format_search_results_json(results)

        # Return based on format parameter
        if format == "json":
            return search_results
        else:
            return MemoryLogFormatter.format_search_results_text(
                search_results,
                search_request.query
            )

    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
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
        POST /memory-logs/search-by-date
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
    """
    try:
        # Create VectorStorageService for semantic search
        vector_service = create_vector_storage_service(
            user_id=search_request.user_id,
            project_id=search_request.project_id,
            embedding_service=request.app.state.embedding_service,
            event_bus=request.app.state.event_bus,
            logger=logger
        )

        # Create service instance
        service = MemoryLogService(None, vector_service, None, logger)

        # Search by date via service
        results = await service.search_by_date(
            query=search_request.query,
            user_id=search_request.user_id,
            project_id=search_request.project_id,
            limit=search_request.limit,
            time_period=search_request.time_period,
            start_date=search_request.start_date,
            end_date=search_request.end_date
        )

        # Format results using formatter
        search_results = MemoryLogFormatter.format_search_results_json(results)

        # Return based on format parameter
        if format == "json":
            return search_results
        else:
            # Generate time period description
            time_period_str = search_request.time_period or f"{search_request.start_date} to {search_request.end_date}"
            return MemoryLogFormatter.format_date_search_text(
                search_results,
                search_request.query,
                time_period_str
            )

    except Exception as e:
        logger.error(f"Date search failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Date search failed: {str(e)}"
        )
