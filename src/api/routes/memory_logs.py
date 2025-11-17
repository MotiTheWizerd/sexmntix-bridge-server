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
    MemoryLogSearchResult
)
from src.database.repositories.memory_log_repository import MemoryLogRepository
from src.modules.core import EventBus, Logger

router = APIRouter(prefix="/memory-logs", tags=["memory-logs"])


@router.post("", response_model=MemoryLogResponse, status_code=201)
async def create_memory_log(
    data: MemoryLogCreate,
    db: AsyncSession = Depends(get_db_session),
    event_bus: EventBus = Depends(get_event_bus),
    logger: Logger = Depends(get_logger),
):
    """
    Create a new memory log with automatic embedding generation via event-driven architecture.

    New Unified Format (same as MCP tool):
    {
        "user_id": 1,
        "project_id": "default",
        "memory_log": {
            "content": "Memory content",
            "task": "bug_fix",
            "agent": "user",
            "tags": ["api", "rest"],
            "metadata": {"source": "web"}
        }
    }

    Hybrid Event-Driven Workflow:
    1. Store memory log in PostgreSQL (synchronous for immediate persistence)
    2. Emit memory_log.stored event with memory_log_id
    3. ChromaDB handler generates embedding and stores vector (async background task)

    This approach ensures data integrity while enabling async vector storage
    for better performance and non-blocking failures.

    User and project IDs enable multi-tenant isolation in vector storage.
    The system automatically adds a datetime field.
    """
    # All fields in memory_log are now optional
    task = data.memory_log.task or ""
    agent = data.memory_log.agent or "mcp_client"
    content = data.memory_log.content or ""

    logger.info(f"Creating memory log for task: {task}")

    # Add datetime field (system-generated)
    from datetime import datetime
    current_datetime = datetime.utcnow()
    current_datetime_iso = current_datetime.isoformat()

    # Build raw_data with new nested structure (same as MCP tool)
    # Format tags as tag_0, tag_1, etc.
    memory_log_data = {
        "task": task,
        "agent": agent,
        "content": content
    }

    # Add formatted tags if provided
    if data.memory_log.tags:
        for i, tag in enumerate(data.memory_log.tags[:5]):  # Max 5 tags
            memory_log_data[f"tag_{i}"] = str(tag)

    # Merge additional metadata if provided
    if data.memory_log.metadata:
        memory_log_data.update(data.memory_log.metadata)

    # Build top-level structure
    raw_data = {
        "user_id": str(data.user_id),
        "project_id": data.project_id,
        "datetime": current_datetime_iso,
        "memory_log": memory_log_data
    }

    # Create memory log in PostgreSQL (synchronous for immediate response with ID)
    repo = MemoryLogRepository(db)
    memory_log = await repo.create(
        task=task,
        agent=agent,
        date=current_datetime,
        raw_data=raw_data,
        user_id=str(data.user_id),
        project_id=data.project_id,
    )

    logger.info(f"Memory log stored in PostgreSQL with id: {memory_log.id}")

    # Emit event for async vector storage (background task via event handler)
    event_data = {
        "memory_log_id": memory_log.id,
        "task": task,
        "agent": agent,
        "date": current_datetime,
        "raw_data": raw_data,
        "user_id": str(data.user_id),
        "project_id": data.project_id,
    }

    # Use publish (not publish_async) to schedule as background task
    # This triggers the memory_log.stored event handler asynchronously
    event_bus.publish("memory_log.stored", event_data)

    logger.info(
        f"Memory log created with id {memory_log.id}, "
        f"vector storage scheduled as background task"
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


@router.post("/search", response_model=List[MemoryLogSearchResult])
async def search_memory_logs(
    search_request: MemoryLogSearchRequest,
    request: Request,
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
    logger.info(
        f"Searching memory logs for: '{search_request.query[:100]}' "
        f"(user: {search_request.user_id}, project: {search_request.project_id})"
    )

    try:
        # Create VectorStorageService for this specific user/project
        vector_service = create_vector_storage_service(
            user_id=search_request.user_id,
            project_id=search_request.project_id,
            embedding_service=request.app.state.embedding_service,
            event_bus=request.app.state.event_bus,
            logger=logger
        )

        # Build combined filter with tag if provided
        combined_filter = search_request.filters or {}
        if search_request.tag:
            # Add tag filter using $or across tag_0 through tag_4
            tag_filter = {
                "$or": [
                    {"tag_0": search_request.tag},
                    {"tag_1": search_request.tag},
                    {"tag_2": search_request.tag},
                    {"tag_3": search_request.tag},
                    {"tag_4": search_request.tag}
                ]
            }
            # Combine with existing filters using $and
            if combined_filter:
                combined_filter = {"$and": [combined_filter, tag_filter]}
            else:
                combined_filter = tag_filter

        results = await vector_service.search_similar_memories(
            query=search_request.query,
            user_id=search_request.user_id,
            project_id=search_request.project_id,
            limit=search_request.limit,
            where_filter=combined_filter,
            min_similarity=search_request.min_similarity
        )

        # Convert to response format
        search_results = []
        for result in results:
            # Extract memory_log_id from the memory_id format: memory_{id}_{user}_{project}
            memory_id_parts = result["id"].split("_")
            memory_log_id = int(memory_id_parts[1]) if len(memory_id_parts) > 1 else None

            search_results.append(
                MemoryLogSearchResult(
                    id=result["id"],
                    memory_log_id=memory_log_id,
                    document=result["document"],
                    metadata=result["metadata"],
                    distance=result["distance"],
                    similarity=result["similarity"]
                )
            )

        logger.info(f"Found {len(search_results)} matching memories")

        return search_results

    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )
