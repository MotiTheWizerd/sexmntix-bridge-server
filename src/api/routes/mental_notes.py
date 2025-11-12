from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from src.api.dependencies.database import get_db_session
from src.api.dependencies.event_bus import get_event_bus
from src.api.dependencies.logger import get_logger
from src.api.schemas.mental_note import MentalNoteCreate, MentalNoteResponse
from src.database.repositories.mental_note_repository import MentalNoteRepository
from src.modules.core import EventBus, Logger

router = APIRouter(prefix="/mental-notes", tags=["mental-notes"])


@router.post("", response_model=MentalNoteResponse, status_code=201)
async def create_mental_note(
    data: MentalNoteCreate,
    db: AsyncSession = Depends(get_db_session),
    event_bus: EventBus = Depends(get_event_bus),
    logger: Logger = Depends(get_logger),
):
    logger.info(f"Creating mental note for session: {data.sessionId}")
    
    raw_data = data.model_dump(mode="json")
    
    repo = MentalNoteRepository(db)
    mental_note = await repo.create(
        session_id=data.sessionId,
        start_time=data.startTime,
        raw_data=raw_data,
    )
    
    event_bus.publish("mental_note.created", {"id": mental_note.id, "session_id": data.sessionId})
    logger.info(f"Mental note created with id: {mental_note.id}")
    
    return mental_note


@router.get("/{id}", response_model=MentalNoteResponse)
async def get_mental_note(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    logger: Logger = Depends(get_logger),
):
    logger.info(f"Fetching mental note: {id}")
    
    repo = MentalNoteRepository(db)
    mental_note = await repo.get_by_id(id)
    
    if not mental_note:
        raise HTTPException(status_code=404, detail="Mental note not found")
    
    return mental_note


@router.get("", response_model=List[MentalNoteResponse])
async def list_mental_notes(
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session),
    logger: Logger = Depends(get_logger),
):
    logger.info(f"Listing mental notes (limit: {limit})")
    
    repo = MentalNoteRepository(db)
    mental_notes = await repo.get_all(limit=limit)
    
    return mental_notes
