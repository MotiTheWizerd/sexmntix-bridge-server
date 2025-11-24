"""
Request/response handlers for mental note operations.

Handles business logic orchestration between services, formatters, and validation.
"""
from typing import List, Union
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.schemas.mental_note import (
    MentalNoteCreate,
    MentalNoteResponse,
    MentalNoteSearchRequest,
    MentalNoteSearchResult,
)
from src.api.routes.mental_notes.formatters import MentalNoteFormatter
from src.database.repositories import MentalNoteRepository
from src.modules.core import EventBus, Logger
from src.modules.embeddings import EmbeddingService


class CreateMentalNoteHandler:
    """Handler for creating mental notes."""

    @staticmethod
    async def handle(
        data: MentalNoteCreate,
        db: AsyncSession,
        event_bus: EventBus,
        logger: Logger,
        embedding_service: EmbeddingService,
    ) -> MentalNoteResponse:
        """
        Handle mental note creation.

        Args:
            data: Mental note creation data
            db: Database session
            event_bus: Event bus for async tasks
            logger: Logger instance
            embedding_service: Embedding generation service

        Returns:
            Created mental note response

        Raises:
            HTTPException: If creation fails
        """
        logger.info(f"Creating mental note for session: {data.sessionId}")

        try:
            # Create repository
            repo = MentalNoteRepository(db)

            # Generate embedding for the mental note content
            embedding_response = await embedding_service.generate_embedding(data.content)
            embedding_vector = embedding_response.embedding

            # Create mental note in PostgreSQL with embedding
            mental_note = await repo.create(
                session_id=data.sessionId,
                content=data.content,
                note_type=data.note_type,
                meta_data=data.meta_data or {},
                user_id=data.user_id,
                project_id=data.project_id,
                embedding=embedding_vector,
            )

            logger.info(f"Mental note stored in PostgreSQL with id: {mental_note.id}")

            # Emit event for async vector storage (background task via event handler)
            event_data = {
                "mental_note_id": mental_note.id,
                "session_id": data.sessionId,
                "content": data.content,
                "note_type": data.note_type,
                "meta_data": data.meta_data or {},
                "user_id": data.user_id,
                "project_id": data.project_id,
            }

            # Use publish to schedule as background task
            event_bus.publish("mental_note.stored", event_data)

            logger.info(
                f"Mental note created with id {mental_note.id}, "
                f"vector storage scheduled as background task"
            )

            return mental_note

        except Exception as e:
            logger.error(f"[HANDLER] Mental note creation failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Mental note creation failed: {str(e)}"
            )


class GetMentalNoteHandler:
    """Handler for fetching mental notes by ID."""

    @staticmethod
    async def handle(
        mental_note_id: str,
        db: AsyncSession,
        logger: Logger
    ) -> MentalNoteResponse:
        """
        Handle mental note retrieval by ID.

        Args:
            mental_note_id: Mental note identifier
            db: Database session
            logger: Logger instance

        Returns:
            Mental note response

        Raises:
            HTTPException: If not found
        """
        logger.info(f"Fetching mental note: {mental_note_id}")

        repo = MentalNoteRepository(db)
        mental_note = await repo.get_by_id(mental_note_id)

        if not mental_note:
            raise HTTPException(status_code=404, detail="Mental note not found")

        return mental_note


class ListMentalNotesHandler:
    """Handler for listing mental notes."""

    @staticmethod
    async def handle(
        limit: int,
        db: AsyncSession,
        logger: Logger
    ) -> List[MentalNoteResponse]:
        """
        Handle mental note listing.

        Args:
            limit: Maximum number of results
            db: Database session
            logger: Logger instance

        Returns:
            List of mental note responses
        """
        logger.info(f"Listing mental notes (limit: {limit})")

        repo = MentalNoteRepository(db)
        mental_notes = await repo.get_all(limit=limit)

        return mental_notes


class SearchMentalNotesHandler:
    """Handler for semantic search of mental notes."""

    @staticmethod
    async def handle(
        search_request: MentalNoteSearchRequest,
        db: AsyncSession,
        logger: Logger,
        embedding_service: EmbeddingService,
    ) -> Union[List[MentalNoteSearchResult], str]:
        """
        Handle mental note semantic search with format support.

        Args:
            search_request: Search request parameters (includes format field)
            db: Database session
            logger: Logger instance
            embedding_service: Embedding generation service

        Returns:
            JSON array or formatted text based on request.format

        Raises:
            HTTPException: If search fails
        """
        logger.info(
            f"Searching mental notes for: '{search_request.query[:100]}' "
            f"(user: {search_request.user_id}, project: {search_request.project_id})"
        )

        try:
            # Generate embedding for the query
            embedding_response = await embedding_service.generate_embedding(search_request.query)
            query_embedding = embedding_response.embedding

            # Search PostgreSQL using pgvector
            repo = MentalNoteRepository(db)
            results = await repo.search_similar(
                query_embedding=query_embedding,
                user_id=search_request.user_id,
                project_id=search_request.project_id,
                limit=search_request.limit,
                min_similarity=search_request.min_similarity
            )

            # Transform results to intermediate format
            search_results = [
                {
                    "id": str(note.id),
                    "mental_note_id": str(note.id),
                    "document": {
                        "content": note.content,
                        "note_type": note.note_type,
                        "session_id": note.session_id,
                        "created_at": note.created_at.isoformat(),
                    },
                    "metadata": {
                        "user_id": note.user_id,
                        "project_id": note.project_id,
                        "meta_data": note.meta_data or {},
                    },
                    "distance": 1.0 - similarity,
                    "similarity": similarity
                }
                for note, similarity in results
            ]

            logger.info(f"Found {len(search_results)} mental notes matching query")

            # Format based on request.format field
            if search_request.format == "text":
                # Return formatted text for terminal/MCP tools
                return MentalNoteFormatter.format_text(search_results, search_request.query)
            else:
                # Return JSON format (default)
                return MentalNoteFormatter.format_json(search_results)

        except Exception as e:
            logger.error(f"[HANDLER] Search failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Search failed: {str(e)}"
            )
