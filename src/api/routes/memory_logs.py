from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from src.api.dependencies.database import get_db_session
from src.api.dependencies.event_bus import get_event_bus
from src.api.dependencies.logger import get_logger
from src.api.schemas.memory_log import MemoryLogCreate, MemoryLogResponse
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
    logger.info(f"Creating memory log for task: {data.task}")
    
    # Convert the entire payload to dict with JSON-serializable values
    raw_data = data.model_dump(mode="json")
    
    repo = MemoryLogRepository(db)
    memory_log = await repo.create(
        task=data.task,
        agent=data.agent,
        date=data.date,
        raw_data=raw_data,
    )
    
    event_bus.publish("memory_log.created", {"id": memory_log.id, "task": data.task})
    logger.info(f"Memory log created with id: {memory_log.id}")
    
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
