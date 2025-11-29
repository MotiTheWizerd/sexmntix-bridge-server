from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.api.dependencies.database import get_db_session
from src.api.dependencies.event_bus import get_event_bus
from src.api.dependencies.logger import get_logger
from src.api.dependencies.vector_storage import create_vector_storage_service
from src.api.schemas.conversation import (
    ConversationCreate,
    ConversationCreateV2,
    ConversationResponse,
    ConversationSearchRequest,
    ConversationSearchResult,
)
from src.api.formatters.conversation_formatter import ConversationFormatter
from src.modules.core import EventBus, Logger

from .service import (
    ConversationOrchestrator,
    build_conversation_service,
    build_vector_search_service,
)


router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("", response_model=ConversationResponse, status_code=201)
async def create_conversation(
    data: ConversationCreate,
    db: AsyncSession = Depends(get_db_session),
    event_bus: EventBus = Depends(get_event_bus),
    logger: Logger = Depends(get_logger),
):
    """Create a new conversation with automatic embedding generation."""
    service = build_conversation_service(db_session=db, event_bus=event_bus, logger=logger)
    conversation = await service.create_conversation(
        conversation_id=data.conversation_id,
        model=data.model,
        conversation_messages=[msg.model_dump() for msg in data.conversation],
        user_id=data.user_id,
        project_id=data.project_id,
        session_id=data.session_id,
    )
    return conversation


@router.post("/raw", response_model=ConversationResponse, status_code=201)
async def create_conversation_raw(
    data: ConversationCreateV2,
    db: AsyncSession = Depends(get_db_session),
    event_bus: EventBus = Depends(get_event_bus),
    logger: Logger = Depends(get_logger),
):
    """Create a new conversation using the `conversation_messages` field.

    This endpoint accepts the same data that the service layer expects and
    will insert the conversation into the DB and schedule vector storage.
    """
    service = build_conversation_service(db_session=db, event_bus=event_bus, logger=logger)
    conversation = await service.create_conversation(
        conversation_id=data.conversation_id,
        model=data.model,
        conversation_messages=[msg.model_dump() for msg in data.conversation_messages],
        user_id=data.user_id,
        project_id=data.project_id,
        session_id=data.session_id,
    )
    return conversation


@router.get("/{id}", response_model=ConversationResponse)
async def get_conversation(
    id: str,
    db: AsyncSession = Depends(get_db_session),
    logger: Logger = Depends(get_logger),
):
    """Retrieve a conversation by database ID."""
    logger.info(f"Fetching conversation: {id}")

    service = build_conversation_service(db_session=db, event_bus=None, logger=logger)
    conversation = await service.repository.get_by_id(id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.get("", response_model=List[ConversationResponse])
async def list_conversations(
    limit: int = 100,
    model: str = None,
    db: AsyncSession = Depends(get_db_session),
    logger: Logger = Depends(get_logger),
):
    """List conversations with optional filtering."""
    logger.info(f"Listing conversations (limit: {limit}, model: {model})")

    service = build_conversation_service(db_session=db, event_bus=None, logger=logger)
    if model:
        conversations = await service.repository.get_by_model(model, limit=limit)
    else:
        conversations = await service.repository.get_all(limit=limit)
    return conversations


@router.post("/search", response_model=List[ConversationSearchResult])
async def search_conversations(
    search_request: ConversationSearchRequest,
    request: Request,
    logger: Logger = Depends(get_logger),
):
    """Semantic search for conversations by meaning."""
    try:
        vector_service = create_vector_storage_service(
            user_id=search_request.user_id,
            project_id=search_request.project_id,
            embedding_service=request.app.state.embedding_service,
            event_bus=request.app.state.event_bus,
            logger=logger,
        )

        service = build_vector_search_service(vector_service=vector_service, logger=logger)
        results = await service.search_conversations(
            query=search_request.query,
            user_id=search_request.user_id,
            project_id=search_request.project_id,
            limit=search_request.limit,
            min_similarity=search_request.min_similarity,
            model=search_request.model,
            session_id=search_request.session_id,
        )

        return ConversationFormatter.format_search_results(results)

    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/fetch-memory")
async def fetch_memory(
    search_request: ConversationSearchRequest,
    request: Request,
    logger: Logger = Depends(get_logger),
):
    """Fetch synthesized memory from conversation search results."""
    try:
        if not search_request.project_id:
            raise HTTPException(status_code=400, detail="project_id is required")

        orchestrator = ConversationOrchestrator(logger=logger)
        logger.info(
            "[FETCH_MEMORY] received request",
            extra={
                "user_id": search_request.user_id,
                "project_id": search_request.project_id,
                "session_id": search_request.session_id,
            },
        )
        return await orchestrator.fetch_memory(search_request, request)
    except Exception as e:
        logger.error(f"Memory fetch failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Memory fetch failed: {str(e)}")
