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
from src.api.schemas.conversation import (
    ConversationCreate,
    ConversationResponse,
    ConversationSearchRequest,
    ConversationSearchResult
)
from src.database.repositories.conversation_repository import ConversationRepository
from src.modules.core import EventBus, Logger
from datetime import datetime


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
    logger.info(f"Creating conversation: {data.conversation_id}")

    # Build raw_data structure
    raw_data = {
        "user_id": data.user_id,
        "project_id": data.project_id,
        "conversation_id": data.conversation_id,
        "model": data.model,
        "conversation": [msg.model_dump() for msg in data.conversation],
        "created_at": datetime.utcnow().isoformat()
    }

    # Create conversation in PostgreSQL (synchronous for immediate response with ID)
    # Note: Allows duplicate conversation_id for versioning/updates
    repo = ConversationRepository(db)

    conversation = await repo.create(
        conversation_id=data.conversation_id,
        model=data.model,
        raw_data=raw_data,
        user_id=data.user_id,
        project_id=data.project_id,
    )

    logger.info(f"Conversation stored in PostgreSQL with id: {conversation.id}")

    # Emit event for async vector storage (background task via event handler)
    event_data = {
        "conversation_db_id": conversation.id,
        "conversation_id": data.conversation_id,
        "model": data.model,
        "raw_data": raw_data,
        "user_id": data.user_id,
        "project_id": data.project_id,
    }

    # Use publish (not publish_async) to schedule as background task
    event_bus.publish("conversation.stored", event_data)

    logger.info(
        f"Conversation created with id {conversation.id}, "
        f"vector storage scheduled as background task (separate collection)"
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
    logger.info(
        f"Searching conversations for: '{search_request.query[:100]}' "
        f"(user: {search_request.user_id})"
    )

    try:
        # Import here to avoid circular dependency
        from src.api.dependencies.vector_storage import create_vector_storage_service

        # Create VectorStorageService for this specific user (conversations are user-scoped)
        vector_service = create_vector_storage_service(
            user_id=search_request.user_id,
            project_id="",  # Empty project_id - conversations are user-scoped only
            embedding_service=request.app.state.embedding_service,
            event_bus=request.app.state.event_bus,
            logger=logger
        )

        # Build filter for model if provided
        combined_filter = {}
        if search_request.model:
            combined_filter["model"] = search_request.model

        # Search conversations using separate collection (user-scoped only)
        results = await vector_service.search_similar_conversations(
            query=search_request.query,
            user_id=search_request.user_id,
            limit=search_request.limit,
            where_filter=combined_filter,
            min_similarity=search_request.min_similarity
        )

        # Convert to response format
        search_results = []
        for result in results:
            # Extract conversation_id from metadata
            conversation_id = result.get("metadata", {}).get("conversation_id")

            search_results.append(
                ConversationSearchResult(
                    id=result["id"],
                    conversation_id=conversation_id,
                    document=result["document"],
                    metadata=result["metadata"],
                    distance=result["distance"],
                    similarity=result["similarity"]
                )
            )

        logger.info(f"Found {len(search_results)} matching conversations")
        return search_results

    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )
