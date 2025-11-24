"""
FastAPI routes for conversation operations.

Provides endpoints for creating, retrieving, and searching conversations.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from src.api.dependencies.database import get_db_session
from src.api.dependencies.event_bus import get_event_bus
from src.api.dependencies.logger import get_logger
from src.api.dependencies.vector_storage import create_vector_storage_service
from src.api.schemas.conversation import (
    ConversationCreate,
    ConversationResponse,
    ConversationSearchRequest,
    ConversationSearchResult
)
from src.api.formatters.conversation_formatter import ConversationFormatter
from src.database.repositories import ConversationRepository
from src.services.conversation_service import ConversationService
from src.modules.core import EventBus, Logger


router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("", response_model=ConversationResponse, status_code=201)
async def create_conversation(
    data: ConversationCreate,
    db: AsyncSession = Depends(get_db_session),
    event_bus: EventBus = Depends(get_event_bus),
    logger: Logger = Depends(get_logger),
):
    """
    Create a new conversation with automatic embedding generation.

    Workflow:
    1. Store conversation in PostgreSQL (synchronous for immediate persistence)
    2. Emit conversation.stored event
    3. Background handler generates embedding and stores in ChromaDB (separate collection)

    Request format:
    {
        "user_id": "1",
        "project_id": "default",
        "conversation_id": "691966a7-318c-8331-b3d0-9862429577c0",
        "model": "gpt-5-1-instant",
        "conversation": [
            {
                "role": "user",
                "message_id": "64ae03ed-597b-4368-aed3-1d1ab6c7745e",
                "text": "one more test"
            },
            {
                "role": "assistant",
                "message_id": "b5e7ff53-3d91-4e6a-bd41-d2fd5e96c937",
                "text": "received."
            }
        ]
    }
    """
    # Create service with required dependencies
    repo = ConversationRepository(db)
    service = ConversationService(
        repository=repo,
        event_bus=event_bus,
        logger=logger
    )

    # Delegate to service layer
    conversation = await service.create_conversation(
        conversation_id=data.conversation_id,
        model=data.model,
        conversation_messages=[msg.model_dump() for msg in data.conversation],
        user_id=data.user_id,
        project_id=data.project_id,
        session_id=data.session_id
    )

    return conversation


@router.get("/{id}", response_model=ConversationResponse)
async def get_conversation(
    id: str,
    db: AsyncSession = Depends(get_db_session),
    logger: Logger = Depends(get_logger),
):
    """
    Retrieve a conversation by database ID.

    Args:
        id: PostgreSQL conversation UUID

    Returns:
        Conversation with all fields including embedding
    """
    logger.info(f"Fetching conversation: {id}")

    repo = ConversationRepository(db)
    conversation = await repo.get_by_id(id)

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
    """
    List conversations with optional filtering.

    Args:
        limit: Maximum number of results (default: 100)
        model: Filter by AI model (optional)

    Returns:
        List of conversations
    """
    logger.info(f"Listing conversations (limit: {limit}, model: {model})")

    repo = ConversationRepository(db)

    if model:
        conversations = await repo.get_by_model(model, limit=limit)
    else:
        conversations = await repo.get_all(limit=limit)

    return conversations


@router.post("/search", response_model=List[ConversationSearchResult])
async def search_conversations(
    search_request: ConversationSearchRequest,
    request: Request,
    logger: Logger = Depends(get_logger),
):
    """
    Semantic search for conversations by meaning.

    Searches the separate conversations_{hash} ChromaDB collection.
    Uses vector embeddings to find similar conversations based on semantic similarity.

    Example:
        POST /conversations/search
        {
            "query": "authentication discussion",
            "user_id": "1",
            "project_id": "default",
            "limit": 5,
            "min_similarity": 0.5,
            "model": "gpt-5-1-instant"
        }

    Returns:
        Conversations ranked by similarity with scores.
    """
    try:
        # Create VectorStorageService for this specific user (conversations are user-scoped)
        vector_service = create_vector_storage_service(
            user_id=search_request.user_id,
            project_id="conversations",  # Dedicated collection for conversations
            embedding_service=request.app.state.embedding_service,
            event_bus=request.app.state.event_bus,
            logger=logger
        )

        # Create service with vector dependencies
        service = ConversationService(
            vector_service=vector_service,
            logger=logger
        )

        # Delegate search to service layer
        results = await service.search_conversations(
            query=search_request.query,
            user_id=search_request.user_id,
            limit=search_request.limit,
            min_similarity=search_request.min_similarity,
            model=search_request.model,
            session_id=search_request.session_id
        )

        # Format results for API response
        search_results = ConversationFormatter.format_search_results(results)

        return search_results

    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


@router.post("/fetch-memory")
async def fetch_memory(
    search_request: ConversationSearchRequest,
    request: Request,
    logger: Logger = Depends(get_logger),
):
    """
    Fetch synthesized memory from conversation search results.

    Workflow:
    1. Perform semantic search (same as /conversations/search)
    2. Send raw search results to Gemini for synthesis
    3. Return only the synthesized natural language memory

    Uses the same parameters as /conversations/search:
    - query: Search query string
    - user_id: User identifier
    - project_id: Project identifier (optional, deprecated)
    - limit: Maximum results (default: 10)
    - min_similarity: Minimum similarity threshold (default: 0.0)
    - model: Filter by AI model (optional)

    Example:
        POST /conversations/fetch-memory
        {
            "query": "authentication discussion",
            "user_id": "1",
            "project_id": "default",
            "limit": 5,
            "min_similarity": 0.5,
            "model": "gpt-5-1-instant"
        }

    Returns:
        {
            "synthesized_memory": "Core Concept: ...\n\nI remember...\n\nKey Association: ..."
        }
    """
    try:
        # Create VectorStorageService for this specific user
        vector_service = create_vector_storage_service(
            user_id=search_request.user_id,
            project_id="conversations",  # Dedicated collection for conversations
            embedding_service=request.app.state.embedding_service,
            event_bus=request.app.state.event_bus,
            logger=logger
        )

        # Create service with vector and LLM dependencies
        llm_service = request.app.state.llm_service
        service = ConversationService(
            vector_service=vector_service,
            llm_service=llm_service,
            logger=logger
        )

        # Delegate memory synthesis to service layer
        synthesized_memory = await service.fetch_synthesized_memory(
            query=search_request.query,
            user_id=search_request.user_id,
            limit=search_request.limit,
            min_similarity=search_request.min_similarity,
            model=search_request.model,
            session_id=search_request.session_id
        )

        # Format response
        return ConversationFormatter.format_memory_response(synthesized_memory)

    except Exception as e:
        logger.error(f"Memory fetch failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Memory fetch failed: {str(e)}"
        )
