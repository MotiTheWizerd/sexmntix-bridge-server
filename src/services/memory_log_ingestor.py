"""
Reusable helper to store memory logs and emit the memory_log.stored event.

Encapsulates the logic previously embedded in the API route so it can be
reused by scripts/CLI tools while keeping the same behavior:
- Normalize/validate dates
- Auto-calculate temporal_context when missing
- Add system datetime and session_id
- Persist via MemoryLogRepository
- Emit memory_log.stored for downstream vectorization
"""

from datetime import datetime
from typing import Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.memory_log import MemoryLogCreate, TemporalContext
from src.database.repositories.memory_log_repository import MemoryLogRepository
from src.modules.core import EventBus, Logger
from src.modules.core.temporal_context import TemporalContextCalculator


async def ingest_memory_log(
    data: MemoryLogCreate,
    db: AsyncSession,
    event_bus: EventBus,
    logger: Logger,
    emit_event: bool = True,
) -> Any:
    """
    Store a memory log and emit memory_log.stored.

    Args:
        data: MemoryLogCreate payload (already validated)
        db: Async SQLAlchemy session
        event_bus: Event bus to publish memory_log.stored
        logger: Logger instance
        emit_event: Whether to publish memory_log.stored (defaults to True)

    Returns:
        The created MemoryLog ORM instance.
    """
    task = data.memory_log.task
    agent = data.memory_log.agent
    date_str = data.memory_log.date

    logger.info(f"Creating memory log for task: {task}")

    # Parse date string to datetime
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        date_datetime = datetime.combine(date_obj, datetime.min.time())
    except ValueError:
        try:
            date_datetime = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            date_obj = date_datetime.date()
        except ValueError:
            raise ValueError(f"Invalid date format: {date_str}. Expected YYYY-MM-DD or ISO format.")

    # Convert memory_log to dict, handling nested models
    memory_log_dict: Dict[str, Any] = data.memory_log.model_dump(exclude_none=True)

    # Calculate temporal_context if not provided
    if "temporal_context" not in memory_log_dict or memory_log_dict["temporal_context"] is None:
        temporal_context_data = TemporalContextCalculator.calculate_temporal_context(date_obj)
        memory_log_dict["temporal_context"] = TemporalContext(**temporal_context_data).model_dump()

    # Add datetime field (system-generated ISO-8601 timestamp)
    current_datetime_iso = datetime.utcnow().isoformat()

    # Build top-level structure with session_id
    raw_data = {
        "user_id": str(data.user_id),
        "project_id": data.project_id,
        "session_id": data.session_id,
        "datetime": current_datetime_iso,
        "memory_log": memory_log_dict,
    }

    # Persist
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

    if emit_event:
        event_data = {
            "memory_log_id": memory_log.id,
            "task": task,
            "agent": agent,
            "date": date_datetime,
            "raw_data": raw_data,
            "user_id": str(data.user_id),
            "project_id": data.project_id,
        }

        event_bus.publish("memory_log.stored", event_data)

        logger.info(
            f"Memory log created with id {memory_log.id}, "
            f"vector storage scheduled as background task"
        )
    else:
        logger.info(
            f"Memory log created with id {memory_log.id}, "
            f"vector storage NOT emitted (emit_event=False)"
        )

    return memory_log
