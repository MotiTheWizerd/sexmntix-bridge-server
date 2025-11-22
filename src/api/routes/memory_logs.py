from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import datetime, timedelta
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
    TemporalContext
)
from src.database.repositories.memory_log_repository import MemoryLogRepository
from src.modules.core import EventBus, Logger
from src.modules.core.temporal_context import TemporalContextCalculator

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

    New Comprehensive Format:
    {
        "user_id": "uuid-string",
        "project_id": "default",
        "session_id": "string",
        "memory_log": {
            "task": "task-name-kebab-case",
            "agent": "claude-sonnet-4",
            "date": "2025-01-15",
            "component": "component-name",
            "temporal_context": {...},  // Auto-calculated if not provided
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
    # Extract required fields
    task = data.memory_log.task
    agent = data.memory_log.agent
    date_str = data.memory_log.date

    logger.info(f"Creating memory log for task: {task}")

    # Parse date string to datetime
    try:
        # Try parsing date string (format: "2025-01-15")
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        date_datetime = datetime.combine(date_obj, datetime.min.time())
    except ValueError:
        # Fallback: try ISO format
        try:
            date_datetime = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            date_obj = date_datetime.date()
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid date format: {date_str}. Expected format: YYYY-MM-DD"
            )

    # Convert memory_log to dict, handling nested models
    memory_log_dict = data.memory_log.model_dump(exclude_none=True)
    
    # Calculate temporal_context if not provided
    if "temporal_context" not in memory_log_dict or memory_log_dict["temporal_context"] is None:
        temporal_context_data = TemporalContextCalculator.calculate_temporal_context(date_obj)
        memory_log_dict['temporal_context'] = temporal_context_data

    # Add datetime field (system-generated ISO-8601 timestamp)
    current_datetime = datetime.utcnow()
    current_datetime_iso = current_datetime.isoformat()

    # Build top-level structure with session_id
    raw_data = {
        "user_id": str(data.user_id),
        "project_id": data.project_id,
        "session_id": data.session_id,
        "datetime": current_datetime_iso,
        "memory_log": memory_log_dict
    }

    # Create memory log in PostgreSQL (synchronous for immediate response with ID)
    repo = MemoryLogRepository(db)
    memory_log = await repo.create(
        task=task,
        agent=agent,
        date=date_datetime,
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
        "date": date_datetime,
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


@router.post("/search")
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
            # Add tag filter - tags are stored in metadata as:
            # 1. tag_0, tag_1, tag_2, tag_3, tag_4 (individual fields)
            # 2. tags (comma-separated string)
            # Check both formats for compatibility
            tag_filter = {
                "$or": [
                    {"tag_0": search_request.tag},
                    {"tag_1": search_request.tag},
                    {"tag_2": search_request.tag},
                    {"tag_3": search_request.tag},
                    {"tag_4": search_request.tag},
                    {"tags": {"$contains": search_request.tag}}  # Check comma-separated string
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
            # Handle both integer IDs and UUID strings
            memory_id_parts = result["id"].split("_")
            if len(memory_id_parts) > 1:
                try:
                    memory_log_id = int(memory_id_parts[1])
                except ValueError:
                    # If not an integer, keep as string (UUID from MCP tools)
                    memory_log_id = memory_id_parts[1]
            else:
                memory_log_id = None

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

        # Format as terminal text
        lines = [
            "=" * 80,
            f"SEARCH RESULTS - {len(search_results)} items",
            f'Query: "{search_request.query}"',
            "=" * 80,
            ""
        ]

        for idx, result in enumerate(search_results, 1):
            doc = result.document
            task = doc.get("task", "untitled-memory")

            lines.append(f"[{idx}/{len(search_results)}] {task}")
            lines.append("-" * 80)
            lines.append(f"Similarity: {result.similarity * 100:.1f}%")

            if doc.get("component"):
                lines.append(f"Component: {doc['component']}")

            if doc.get("date"):
                date_str = str(doc['date']).split("T")[0]
                lines.append(f"Date: {date_str}")

            if doc.get("tags"):
                tag_str = ", ".join(doc['tags'][:5])
                lines.append(f"Tags: {tag_str}")

            lines.append("")
            if doc.get("summary"):
                summary = doc['summary']
                if len(summary) > 200:
                    summary = summary[:197] + "..."
                lines.append(summary)

            lines.append("")

        lines.append("=" * 80)
        lines.append("End of Results")
        lines.append("=" * 80)

        formatted_text = "\n".join(lines)
        return PlainTextResponse(content=formatted_text)

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
    db: AsyncSession = Depends(get_db_session),
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
    logger.info(
        f"Searching memory logs by date for: '{search_request.query[:100]}' "
        f"(user: {search_request.user_id}, project: {search_request.project_id})"
    )

    try:
        # Calculate date range based on time_period or use explicit dates
        start_date = search_request.start_date
        end_date = search_request.end_date

        if search_request.time_period:
            now = datetime.utcnow()

            if search_request.time_period == "recent" or search_request.time_period == "last-week":
                # Last 7 days
                start_date = now - timedelta(days=7)
                end_date = now
            elif search_request.time_period == "last-month":
                # Last 30 days
                start_date = now - timedelta(days=30)
                end_date = now
            elif search_request.time_period == "archived":
                # Older than 30 days
                end_date = now - timedelta(days=30)
                start_date = None  # No lower bound for archived

        # Query database by date range
        repo = MemoryLogRepository(db)

        if start_date and end_date:
            memory_logs = await repo.get_by_date_range(
                start_date=start_date,
                end_date=end_date,
                limit=search_request.limit
            )
        elif end_date:
            # Only end_date (archived case)
            memory_logs = await repo.get_by_date_range(
                start_date=datetime.min,
                end_date=end_date,
                limit=search_request.limit
            )
        else:
            # No date filter, just get recent ones
            memory_logs = await repo.get_all(limit=search_request.limit)

        # Optionally filter by semantic similarity if query provided
        # For now, just return the date-filtered results
        # Future: Could integrate with vector search for hybrid date+semantic filtering

        # Create VectorStorageService for semantic search within date-filtered results
        vector_service = create_vector_storage_service(
            user_id=search_request.user_id,
            project_id=search_request.project_id,
            embedding_service=request.app.state.embedding_service,
            event_bus=request.app.state.event_bus,
            logger=logger
        )

        # Build ChromaDB filter for date range
        where_filter = {}
        if start_date:
            where_filter["date"] = {"$gte": start_date.isoformat()}
        if end_date and start_date:
            where_filter["date"] = {
                "$gte": start_date.isoformat(),
                "$lte": end_date.isoformat()
            }
        elif end_date:
            where_filter["date"] = {"$lte": end_date.isoformat()}

        # Perform semantic search with date filter
        results = await vector_service.search_similar_memories(
            query=search_request.query,
            user_id=search_request.user_id,
            project_id=search_request.project_id,
            limit=search_request.limit,
            where_filter=where_filter if where_filter else None,
            min_similarity=0.0
        )

        # Convert to response format
        search_results = []
        for result in results:
            # Extract memory_log_id from the memory_id format
            memory_id_parts = result["id"].split("_")
            if len(memory_id_parts) > 1:
                try:
                    memory_log_id = int(memory_id_parts[1])
                except ValueError:
                    memory_log_id = memory_id_parts[1]
            else:
                memory_log_id = None

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

        # Format as terminal text
        time_period_str = search_request.time_period or f"{start_date} to {end_date}"
        lines = [
            "=" * 80,
            f"DATE-FILTERED SEARCH RESULTS - {len(search_results)} items",
            f'Query: "{search_request.query}"',
            f'Time Period: {time_period_str}',
            "=" * 80,
            ""
        ]

        for idx, result in enumerate(search_results, 1):
            doc = result.document
            task = doc.get("task", "untitled-memory")

            lines.append(f"[{idx}/{len(search_results)}] {task}")
            lines.append("-" * 80)
            lines.append(f"Similarity: {result.similarity * 100:.1f}%")

            if doc.get("component"):
                lines.append(f"Component: {doc['component']}")

            if doc.get("date"):
                date_str = str(doc['date']).split("T")[0]
                lines.append(f"Date: {date_str}")

            if doc.get("tags"):
                tag_str = ", ".join(doc['tags'][:5])
                lines.append(f"Tags: {tag_str}")

            lines.append("")
            if doc.get("summary"):
                summary = doc['summary']
                if len(summary) > 200:
                    summary = summary[:197] + "..."
                lines.append(summary)

            lines.append("")

        lines.append("=" * 80)
        lines.append("End of Results")
        lines.append("=" * 80)

        formatted_text = "\n".join(lines)
        return PlainTextResponse(content=formatted_text)

    except Exception as e:
        logger.error(f"Date search failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Date search failed: {str(e)}"
        )
