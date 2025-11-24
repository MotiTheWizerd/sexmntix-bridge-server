"""
Mental notes API routes - Thin orchestration layer.

Routes delegate to handlers for business logic orchestration.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from src.api.dependencies.database import get_db_session
from src.api.dependencies.event_bus import get_event_bus
from src.api.dependencies.logger import get_logger
from src.api.dependencies.embedding import get_embedding_service
from src.api.schemas.mental_note import (
    MentalNoteCreate,
    MentalNoteResponse,
    MentalNoteSearchRequest,
    MentalNoteSearchResult,
)
from src.api.routes.mental_notes.handlers import (
    CreateMentalNoteHandler,
    GetMentalNoteHandler,
    ListMentalNotesHandler,
    SearchMentalNotesHandler,
)
from src.modules.core import EventBus, Logger
from src.modules.embeddings import EmbeddingService

router = APIRouter(prefix="/mental-notes", tags=["mental-notes"])


@router.post("", response_model=MentalNoteResponse, status_code=201)
async def create_mental_note(
    data: MentalNoteCreate,
    db: AsyncSession = Depends(get_db_session),
    event_bus: EventBus = Depends(get_event_bus),
    logger: Logger = Depends(get_logger),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
):
    """
    Create a new mental note with embedding stored in PostgreSQL.

    Mental notes are timestamped observations, thoughts, or reflections organized
    by session ID. They track context, decisions, or insights during conversations.

    Format:
    {
        "sessionId": "string",
        "content": "string",
        "note_type": "note|decision|observation|insight",
        "user_id": "uuid-string",
        "project_id": "default",
        "meta_data": {}
    }

    Workflow:
    1. Store mental note in PostgreSQL with embedding (synchronous)
    2. Emit mental_note.stored event
    3. ChromaDB handler stores vector (async background task)
    """
    return await CreateMentalNoteHandler.handle(
        data, db, event_bus, logger, embedding_service
    )


@router.get("/{id}", response_model=MentalNoteResponse)
async def get_mental_note(
    id: str,
    db: AsyncSession = Depends(get_db_session),
    logger: Logger = Depends(get_logger),
):
    """Fetch a mental note by ID."""
    return await GetMentalNoteHandler.handle(id, db, logger)


@router.get("", response_model=List[MentalNoteResponse])
async def list_mental_notes(
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session),
    logger: Logger = Depends(get_logger),
):
    """List mental notes with optional limit."""
    return await ListMentalNotesHandler.handle(limit, db, logger)


@router.post("/search")
async def search_mental_notes(
    search_request: MentalNoteSearchRequest,
    db: AsyncSession = Depends(get_db_session),
    logger: Logger = Depends(get_logger),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
):
    """
    Semantic search for mental notes by meaning, not keywords.

    Uses PostgreSQL pgvector for semantic similarity search.
    Mental notes are scoped by user_id and project_id.

    Example:
        POST /mental-notes/search
        {
            "query": "bug fix discussion",
            "user_id": "user123",
            "project_id": "default",
            "limit": 10,
            "min_similarity": 0.5,
            "format": "text"
        }

    Returns mental notes ranked by similarity with scores.
    Format options: 'json' (complete JSON objects, default) or 'text' (formatted terminal output).
    """
    return await SearchMentalNotesHandler.handle(
        search_request, db, logger, embedding_service
    )
