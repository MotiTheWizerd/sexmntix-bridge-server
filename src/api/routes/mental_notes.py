from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from src.api.dependencies.database import get_db_session
from src.api.dependencies.event_bus import get_event_bus
from src.api.dependencies.logger import get_logger
from src.api.dependencies.embedding import get_embedding_service
from src.api.dependencies.vector_storage import create_vector_storage_service
from src.api.schemas.mental_note import (
    MentalNoteCreate,
    MentalNoteResponse,
    MentalNoteSearchRequest,
    MentalNoteSearchResult
)
from src.database.repositories.mental_note_repository import MentalNoteRepository
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
    """Create a new mental note with embedding stored in PostgreSQL."""
    logger.info(f"Creating mental note for session: {data.sessionId}")

    # Build raw_data from input
    raw_data = data.model_dump(mode="json")
    logger.info(f"[EMBEDDING DEBUG] raw_data: {raw_data}")

    # Generate embedding from content
    content = raw_data.get("content", "")
    logger.info(f"[EMBEDDING DEBUG] Extracted content: '{content}'")

    embedding_result = await embedding_service.generate_embedding(content)
    embedding_vector = embedding_result.embedding
    logger.info(f"[EMBEDDING DEBUG] Generated embedding - type: {type(embedding_vector)}, length: {len(embedding_vector) if embedding_vector else 'None'}, first 5 values: {embedding_vector[:5] if embedding_vector else 'None'}")

    # Create mental note in PostgreSQL with embedding
    repo = MentalNoteRepository(db)
    logger.info(f"[EMBEDDING DEBUG] Calling repo.create with embedding of length: {len(embedding_vector) if embedding_vector else 'None'}")

    mental_note = await repo.create(
        session_id=data.sessionId,
        start_time=data.startTime,
        raw_data=raw_data,
        user_id=data.user_id,
        project_id=data.project_id,
        embedding=embedding_vector,
    )

    logger.info(f"[EMBEDDING DEBUG] Mental note created - id: {mental_note.id}, has embedding: {mental_note.embedding is not None}, embedding type: {type(mental_note.embedding)}")
    logger.info(f"Mental note stored in PostgreSQL with id: {mental_note.id}")

    # Emit event for async vector storage (background task via event handler)
    event_data = {
        "mental_note_id": mental_note.id,
        "session_id": data.sessionId,
        "start_time": data.startTime,
        "raw_data": raw_data,
        "user_id": data.user_id,
        "project_id": data.project_id,
    }

    # Use publish to schedule as background task
    # This triggers the mental_note.stored event handler asynchronously
    event_bus.publish("mental_note.stored", event_data)

    logger.info(
        f"Mental note created with id {mental_note.id}, "
        f"vector storage scheduled as background task"
    )

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


@router.post("/search", response_model=List[MentalNoteSearchResult])
async def search_mental_notes(
    search_request: MentalNoteSearchRequest,
    logger: Logger = Depends(get_logger),
    event_bus: EventBus = Depends(get_event_bus),
):
    """
    Semantic search for mental notes by meaning, not keywords.

    Uses vector embeddings to find similar mental notes based on semantic similarity.
    Each user/project gets their own isolated ChromaDB database.
    Can optionally filter by session_id or note_type.

    Example:
        POST /mental-notes/search
        {
            "query": "bug fix discussion",
            "session_id": "session_123",  # optional
            "user_id": "1",
            "project_id": "default",
            "limit": 10,
            "min_similarity": 0.5,
            "note_type": "decision"  # optional
        }

    Returns mental notes ranked by similarity with scores.
    """
    from src.api.dependencies.embedding_service import get_embedding_service
    from fastapi import Request

    logger.info(
        f"Searching mental notes for: '{search_request.query[:100]}' "
        f"(user: {search_request.user_id}, project: {search_request.project_id})"
    )

    try:
        # Get embedding service from app state
        # For now, we'll create it manually - this should be injected via dependency
        from src.modules.embeddings import EmbeddingService
        from src.modules.embeddings.providers.google import GoogleEmbeddingProvider
        from src.modules.embeddings.caching import EmbeddingCache
        from src.modules.core.telemetry import Logger as TelemetryLogger

        # Create embedding service (this should be dependency injected in production)
        provider = GoogleEmbeddingProvider()
        cache = EmbeddingCache()
        embedding_logger = TelemetryLogger("embedding_service")
        embedding_service = EmbeddingService(provider, cache, event_bus, embedding_logger)

        # Create VectorStorageService for this specific user/project
        vector_service = create_vector_storage_service(
            user_id=search_request.user_id,
            project_id=search_request.project_id,
            embedding_service=embedding_service,
            event_bus=event_bus,
            logger=logger
        )

        # Perform semantic search using search_mental_notes method
        results = await vector_service.search_mental_notes(
            query=search_request.query,
            user_id=search_request.user_id,
            project_id=search_request.project_id,
            limit=search_request.limit,
            session_id=search_request.session_id if search_request.session_id else None,
            note_type=search_request.note_type if search_request.note_type else None,
            min_similarity=search_request.min_similarity
        )

        logger.info(f"Found {len(results)} mental notes matching query")
        return results

    except Exception as e:
        logger.error(f"Error searching mental notes: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
