"""
Store Mental Note Tool Implementation

Main tool class that orchestrates mental note storage using modular components.
"""

from typing import Dict, Any
import os
from src.modules.xcp_server.tools.base import BaseTool, ToolDefinition, ToolResult
from src.modules.xcp_server.models.config import ToolContext
from src.modules.xcp_server.exceptions import XCPToolExecutionError
from src.modules.core import EventBus, Logger
from src.database.repositories.mental_note_repository import MentalNoteRepository
from src.modules.embeddings.providers.google import GoogleEmbeddingProvider
from src.modules.embeddings.models import ProviderConfig
from src.modules.embeddings.caching import EmbeddingCache
from src.modules.embeddings import EmbeddingService

from .config import StoreMentalNoteConfig
from .validators import ArgumentValidator
from .formatters import MentalNoteFormatter


class StoreMentalNoteTool(BaseTool):
    """Tool for storing mental notes

    This tool allows AI assistants to store mental notes - timestamped observations,
    thoughts, or reflections organized by session. Mental notes are useful for
    tracking conversation context, decisions, or insights within a session.

    Delegates to specialized components:
    - StoreMentalNoteConfig: Tool definition and constants
    - ArgumentValidator: Argument validation and extraction
    - MentalNoteFormatter: Result formatting
    """

    def __init__(
        self,
        event_bus: EventBus,
        logger: Logger,
        db_session_factory
    ):
        """Initialize store mental note tool

        Args:
            event_bus: Event bus for publishing events
            logger: Logger instance
            db_session_factory: Factory function to create database sessions
        """
        super().__init__(event_bus, logger)
        self.db_session_factory = db_session_factory

        # Initialize embedding service
        embedding_config = ProviderConfig(
            provider_name="google",
            model_name="models/text-embedding-004",
            api_key=os.getenv("GOOGLE_API_KEY"),
            timeout_seconds=30.0,
            max_retries=3
        )
        provider = GoogleEmbeddingProvider(embedding_config)
        cache = EmbeddingCache()
        self.embedding_service = EmbeddingService(
            event_bus=event_bus,
            logger=logger,
            provider=provider,
            cache=cache,
            cache_enabled=True
        )

        # Initialize components
        self.config = StoreMentalNoteConfig()
        self.validator = ArgumentValidator()
        self.formatter = MentalNoteFormatter()

    def get_definition(self) -> ToolDefinition:
        """Get tool definition for MCP registration

        Returns:
            ToolDefinition: Tool metadata and parameter schema
        """
        return self.config.get_tool_definition()

    async def execute(
        self,
        context: ToolContext,
        arguments: Dict[str, Any]
    ) -> ToolResult:
        """Execute mental note storage

        Args:
            context: Execution context
            arguments: Raw arguments from client

        Returns:
            ToolResult: Storage result with mental note ID
        """
        try:
            # Validate and extract arguments
            validated = self._validate_arguments(arguments, context)

            # Log execution details
            self._log_storage_execution(validated, context)

            # Build raw_data structure
            raw_data = self._build_raw_data(validated, context)

            # Store mental note in database
            mental_note = await self._store_note(validated, raw_data, context)

            # Publish event for async vector storage
            self._publish_creation_event(mental_note, validated, raw_data, context)

            # Format and return response
            return self._format_response(mental_note, validated, raw_data, context)

        except ValueError as e:
            # Validation errors return non-exceptional failures
            self.logger.warning(f"Validation error: {str(e)}")
            return ToolResult(
                success=False,
                error=str(e),
                error_code="VALIDATION_ERROR"
            )

        except Exception as e:
            # Unexpected errors are raised as tool execution errors
            self.logger.exception(f"Mental note storage failed: {str(e)}")
            raise XCPToolExecutionError(
                tool_name=self.config.TOOL_NAME,
                message=f"Failed to store mental note: {str(e)}",
                original_error=e
            )

    def _validate_arguments(
        self,
        arguments: Dict[str, Any],
        context: ToolContext
    ) -> Dict[str, Any]:
        """Validate arguments using ArgumentValidator

        Args:
            arguments: Raw arguments from client
            context: Execution context

        Returns:
            Validated arguments dictionary

        Raises:
            ValueError: If validation fails
        """
        return self.validator.extract_and_validate(
            arguments,
            context_session_id=getattr(context, 'session_id', None)
        )

    def _log_storage_execution(
        self,
        validated: Dict[str, Any],
        context: ToolContext
    ) -> None:
        """Log storage execution details

        Args:
            validated: Validated arguments
            context: Execution context
        """
        self.logger.info(
            "Storing mental note",
            extra={
                "session_id": validated["session_id"],
                "note_type": validated["note_type"],
                "user_id": validated["user_id"],
                "project_id": validated["project_id"]
            }
        )

    def _build_raw_data(
        self,
        validated: Dict[str, Any],
        context: ToolContext
    ) -> Dict[str, Any]:
        """Build raw_data structure for database storage

        Args:
            validated: Validated arguments
            context: Execution context

        Returns:
            Complete raw_data dictionary
        """
        return self.formatter.create_raw_data(
            content=validated["content"],
            session_id=validated["session_id"],
            note_type=validated["note_type"],
            user_id=validated["user_id"],
            project_id=validated["project_id"],
            metadata=validated["metadata"]
        )

    async def _store_note(
        self,
        validated: Dict[str, Any],
        raw_data: Dict[str, Any],
        context: ToolContext
    ):
        """Store mental note in database with embedding

        Args:
            validated: Validated arguments
            raw_data: Complete raw_data structure
            context: Execution context with user_id and project_id

        Returns:
            Stored mental note model
        """
        # Generate embedding from content
        content = validated["content"]
        embedding_result = await self.embedding_service.generate_embedding(content)
        embedding_vector = embedding_result.embedding

        self.logger.info(f"Generated embedding for mental note - length: {len(embedding_vector) if embedding_vector else 'None'}")

        async with self.db_session_factory() as db_session:
            repo = MentalNoteRepository(db_session)

            mental_note = await repo.create(
                session_id=validated["session_id"],
                start_time=raw_data["startTime"],
                raw_data=raw_data,
                user_id=validated["user_id"],
                project_id=validated["project_id"],
                embedding=embedding_vector
            )

            self.logger.info(f"Mental note stored with id: {mental_note.id}, embedding: {mental_note.embedding is not None}")
            return mental_note

    def _publish_creation_event(
        self,
        mental_note: Any,
        validated: Dict[str, Any],
        raw_data: Dict[str, Any],
        context: ToolContext
    ) -> None:
        """Publish mental note stored event for async vector storage

        Args:
            mental_note: Stored mental note model
            validated: Validated arguments
            raw_data: Complete raw_data structure
            context: Execution context
        """
        event_data = {
            "mental_note_id": mental_note.id,
            "session_id": validated["session_id"],
            "start_time": raw_data["startTime"],
            "raw_data": raw_data,
            "user_id": validated["user_id"],
            "project_id": validated["project_id"],
        }

        # Publish mental_note.stored event (not mental_note.created)
        # This triggers the MentalNoteStorageHandlers to generate embeddings
        # and store in ChromaDB as a background task
        self.event_bus.publish("mental_note.stored", event_data)

    def _format_response(
        self,
        mental_note: Any,
        validated: Dict[str, Any],
        raw_data: Dict[str, Any],
        context: ToolContext
    ) -> ToolResult:
        """Format storage result into ToolResult

        Args:
            mental_note: Stored mental note model
            validated: Validated arguments
            raw_data: Complete raw_data structure
            context: Execution context

        Returns:
            ToolResult with formatted data
        """
        response_data = self.formatter.create_response_data(
            mental_note_id=mental_note.id,
            session_id=validated["session_id"],
            content=validated["content"],
            note_type=validated["note_type"],
            start_time=raw_data["startTime"],
            created_at=mental_note.created_at.isoformat(),
            user_id=validated["user_id"],
            project_id=validated["project_id"]
        )

        return ToolResult(success=True, data=response_data)
