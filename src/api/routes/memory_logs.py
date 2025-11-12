from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from src.api.dependencies.database import get_db_session
from src.api.dependencies.event_bus import get_event_bus
from src.api.dependencies.logger import get_logger
from src.api.dependencies.vector_storage import get_vector_storage_service
from src.api.schemas.memory_log import (
    MemoryLogCreate,
    MemoryLogResponse,
    MemoryLogSearchRequest,
    MemoryLogSearchResult
)
from src.database.repositories.memory_log_repository import MemoryLogRepository
from src.modules.core import EventBus, Logger
from src.services.vector_storage_service import VectorStorageService

router = APIRouter(prefix="/memory-logs", tags=["memory-logs"])


@router.post("", response_model=MemoryLogResponse, status_code=201)
async def create_memory_log(
    data: MemoryLogCreate,
    db: AsyncSession = Depends(get_db_session),
    event_bus: EventBus = Depends(get_event_bus),
    logger: Logger = Depends(get_logger),
    vector_service: VectorStorageService = Depends(get_vector_storage_service),
):
    """
    Create a new memory log with automatic embedding generation.

    Workflow:
    1. Store memory log in PostgreSQL
    2. Generate embedding from searchable text
    3. Store embedding in PostgreSQL
    4. Store vector in ChromaDB for semantic search

    User and project IDs enable multi-tenant isolation.
    """
    logger.info(f"Creating memory log for task: {data.task}")

    # Convert the entire payload to dict with JSON-serializable values
    raw_data = data.model_dump(mode="json")

    # Create initial memory log in PostgreSQL (without embedding yet)
    repo = MemoryLogRepository(db)
    memory_log = await repo.create(
        task=data.task,
        agent=data.agent,
        date=data.date,
        raw_data=raw_data,
        user_id=data.user_id,
        project_id=data.project_id,
    )

    event_bus.publish("memory_log.created", {"id": memory_log.id, "task": data.task})
    logger.info(f"Memory log created with id: {memory_log.id}")

    # Generate and store vector embedding (if user_id and project_id provided)
    if data.user_id and data.project_id:
        try:
            memory_id, embedding = await vector_service.store_memory_vector(
                memory_log_id=memory_log.id,
                memory_data=raw_data,
                user_id=data.user_id,
                project_id=data.project_id
            )

            # Update memory log with embedding in PostgreSQL
            memory_log = await repo.update(
                id=memory_log.id,
                embedding=embedding
            )

            logger.info(
                f"Vector stored: {memory_id} for memory_log {memory_log.id}"
            )
        except Exception as e:
            logger.error(f"Failed to store vector for memory_log {memory_log.id}: {e}")
            # Continue without embedding - non-blocking failure
    else:
        logger.warning(
            f"Skipping vector storage: user_id or project_id not provided "
            f"for memory_log {memory_log.id}"
        )

    return memory_log


@router.get("/{id}", response_model=MemoryLogResponse)
async def get_memory_log(
    id: int,
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
    vector_service: VectorStorageService = Depends(get_vector_storage_service),
    logger: Logger = Depends(get_logger),
):
    """
    Semantic search for memory logs by meaning, not keywords.

    Uses vector embeddings to find similar memories based on semantic similarity.

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
        results = await vector_service.search_similar_memories(
            query=search_request.query,
            user_id=search_request.user_id,
            project_id=search_request.project_id,
            limit=search_request.limit,
            where_filter=search_request.filters,
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
