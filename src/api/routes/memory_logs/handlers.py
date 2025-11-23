"""
Request/response handlers for memory log operations.

Handles business logic orchestration between services, formatters, and validation.
"""
from typing import List, Union, Dict, Any
from fastapi import Request, HTTPException
from fastapi.responses import PlainTextResponse
from src.api.schemas.memory_log import (
    MemoryLogCreate,
    MemoryLogResponse,
    MemoryLogSearchRequest,
    MemoryLogSearchResult,
    MemoryLogDateSearchRequest,
)
from src.api.routes.memory_logs.formatters import MemoryLogFormatter
from src.database.repositories.memory_log_repository import MemoryLogRepository
from src.services.memory_log_service import MemoryLogService
from src.modules.core import Logger


class CreateMemoryLogHandler:
    """Handler for creating memory logs."""

    @staticmethod
    async def handle(
        request: Request,
        service: MemoryLogService,
        logger: Logger
    ) -> MemoryLogResponse:
        """
        Handle memory log creation.

        Args:
            request: FastAPI request
            service: Memory log service
            logger: Logger instance

        Returns:
            Created memory log response

        Raises:
            HTTPException: If creation fails
        """
        try:
            # Get request body
            body = await request.json()
            logger.debug("[HANDLER] Unwrapping request body")

            # Unwrap request body (handles MCP-wrapped format)
            data_dict = service.unwrap_request_body(body)

            # Validate with Pydantic
            data = MemoryLogCreate(**data_dict)
            logger.debug(f"[HANDLER] Validated: task={data.task}, agent={data.agent}")

            # Convert memory_log to dict, handling nested models
            memory_log_dict = data.memory_log.model_dump(exclude_none=True)

            # Create memory log via service
            memory_log = await service.create_memory_log(
                task=data.task,
                agent=data.agent,
                session_id=data.session_id,
                memory_log=memory_log_dict,
                user_id=str(data.user_id),
                project_id=data.project_id,
            )

            return memory_log

        except Exception as e:
            logger.error(f"[HANDLER] Memory log creation failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Memory log creation failed: {str(e)}"
            )


class GetMemoryLogHandler:
    """Handler for fetching memory logs by ID."""

    @staticmethod
    async def handle(
        memory_log_id: str,
        repository: MemoryLogRepository,
        logger: Logger
    ) -> MemoryLogResponse:
        """
        Handle memory log retrieval by ID.

        Args:
            memory_log_id: Memory log identifier
            repository: Memory log repository
            logger: Logger instance

        Returns:
            Memory log response

        Raises:
            HTTPException: If not found
        """
        logger.info(f"[HANDLER] Fetching memory log: {memory_log_id}")

        memory_log = await repository.get_by_id(memory_log_id)

        if not memory_log:
            raise HTTPException(status_code=404, detail="Memory log not found")

        return memory_log


class ListMemoryLogsHandler:
    """Handler for listing memory logs."""

    @staticmethod
    async def handle(
        limit: int,
        repository: MemoryLogRepository,
        logger: Logger
    ) -> List[MemoryLogResponse]:
        """
        Handle memory log listing.

        Args:
            limit: Maximum number of results
            repository: Memory log repository
            logger: Logger instance

        Returns:
            List of memory log responses
        """
        logger.info(f"[HANDLER] Listing memory logs (limit: {limit})")

        memory_logs = await repository.get_all(limit=limit)

        return memory_logs


class SearchMemoryLogHandler:
    """Handler for semantic search of memory logs."""

    @staticmethod
    async def handle(
        search_request: MemoryLogSearchRequest,
        service: MemoryLogService,
        logger: Logger
    ) -> Union[List[MemoryLogSearchResult], PlainTextResponse]:
        """
        Handle memory log semantic search with format support.

        Args:
            search_request: Search request parameters (includes format field)
            service: Memory log service with vector search
            logger: Logger instance

        Returns:
            JSON array or formatted text based on request.format

        Raises:
            HTTPException: If search fails
        """
        try:
            # Search via service
            results = await service.search_memory_logs(
                query=search_request.query,
                user_id=search_request.user_id,
                project_id=search_request.project_id,
                limit=search_request.limit,
                filters=search_request.filters,
                tag=search_request.tag,
                min_similarity=search_request.min_similarity
            )

            # Format based on request.format field
            if search_request.format == "text":
                # Return raw string for MCP tools (maintains newlines)
                formatted_text = MemoryLogFormatter.format_text(results, search_request.query)
                return formatted_text
            else:
                return MemoryLogFormatter.format_json(results)

        except Exception as e:
            logger.error(f"[HANDLER] Search failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Search failed: {str(e)}"
            )


class DateSearchMemoryLogHandler:
    """Handler for date-filtered semantic search of memory logs."""

    @staticmethod
    async def handle(
        search_request: MemoryLogDateSearchRequest,
        service: MemoryLogService,
        logger: Logger
    ) -> Union[List[MemoryLogSearchResult], PlainTextResponse]:
        """
        Handle memory log date-filtered search with format support.

        Args:
            search_request: Date search request parameters (includes format field)
            service: Memory log service with vector search
            logger: Logger instance

        Returns:
            JSON array or formatted text based on request.format

        Raises:
            HTTPException: If search fails
        """
        try:
            # Search by date via service
            results = await service.search_by_date(
                query=search_request.query,
                user_id=search_request.user_id,
                project_id=search_request.project_id,
                limit=search_request.limit,
                time_period=search_request.time_period,
                start_date=search_request.start_date,
                end_date=search_request.end_date
            )

            # Format based on request.format field
            if search_request.format == "text":
                # Return raw string for MCP tools (maintains newlines)
                formatted_text = MemoryLogFormatter.format_text(results, search_request.query)
                return formatted_text
            else:
                return MemoryLogFormatter.format_json(results)

        except Exception as e:
            logger.error(f"[HANDLER] Date search failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Date search failed: {str(e)}"
            )
