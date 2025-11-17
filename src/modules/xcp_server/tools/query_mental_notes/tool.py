"""
Query Mental Notes Tool Implementation

Main tool class that orchestrates mental note queries using modular components.
"""

from typing import Dict, Any
from src.modules.xcp_server.tools.base import BaseTool, ToolDefinition, ToolResult
from src.modules.xcp_server.models.config import ToolContext
from src.modules.xcp_server.exceptions import XCPToolExecutionError
from src.modules.core import EventBus, Logger
from src.database.repositories.mental_note_repository import MentalNoteRepository

from .config import QueryMentalNotesConfig
from .validators import ArgumentValidator
from .formatters import MentalNoteFormatter


class QueryMentalNotesTool(BaseTool):
    """Tool for querying mental notes

    This tool allows AI assistants to retrieve mental notes by session ID
    or get all notes within a limit. Useful for reviewing context, decisions,
    or insights from previous interactions.

    Delegates to specialized components:
    - QueryMentalNotesConfig: Tool definition and constants
    - ArgumentValidator: Argument validation and extraction
    - MentalNoteFormatter: Result formatting
    """

    def __init__(
        self,
        event_bus: EventBus,
        logger: Logger,
        db_session_factory
    ):
        """Initialize query mental notes tool

        Args:
            event_bus: Event bus for publishing events
            logger: Logger instance
            db_session_factory: Factory function to create database sessions
        """
        super().__init__(event_bus, logger)
        self.db_session_factory = db_session_factory

        # Initialize components
        self.config = QueryMentalNotesConfig()
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
        """Execute mental notes query

        Args:
            context: Execution context
            arguments: Raw arguments from client

        Returns:
            ToolResult: List of mental notes matching the criteria
        """
        try:
            # Validate and extract arguments
            validated = self._validate_arguments(arguments)

            # Log execution details
            self._log_query_execution(validated, context)

            # Perform database query
            mental_notes = await self._perform_query(validated)

            # Format and return response
            return self._format_response(mental_notes, validated, context)

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
            self.logger.exception(f"Mental notes query failed: {str(e)}")
            raise XCPToolExecutionError(
                tool_name=self.config.TOOL_NAME,
                message=f"Failed to query mental notes: {str(e)}",
                original_error=e
            )

    def _validate_arguments(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Validate arguments using ArgumentValidator

        Args:
            arguments: Raw arguments from client

        Returns:
            Validated arguments dictionary

        Raises:
            ValueError: If validation fails
        """
        return self.validator.extract_and_validate(arguments)

    def _log_query_execution(
        self,
        validated: Dict[str, Any],
        context: ToolContext
    ) -> None:
        """Log query execution details

        Args:
            validated: Validated arguments
            context: Execution context
        """
        self.logger.info(
            "Querying mental notes",
            extra={
                "session_id": validated["session_id"],
                "mental_note_id": validated["mental_note_id"],
                "limit": validated["limit"],
                "user_id": validated["user_id"],
                "project_id": validated["project_id"]
            }
        )

    async def _perform_query(self, validated: Dict[str, Any]) -> list:
        """Perform database query for mental notes

        Args:
            validated: Validated arguments

        Returns:
            List of mental note models
        """
        session_id = validated["session_id"]
        mental_note_id = validated["mental_note_id"]
        limit = validated["limit"]

        async with self.db_session_factory() as db_session:
            repo = MentalNoteRepository(db_session)

            # Query by specific ID
            if mental_note_id:
                note = await repo.get_by_id(mental_note_id)
                mental_notes = [note] if note else []

            # Query by session ID
            elif session_id:
                mental_notes = await repo.get_by_session_id(session_id)
                # Apply limit
                mental_notes = mental_notes[:limit]

            # Get all recent notes
            else:
                mental_notes = await repo.get_all(limit=limit)

            self.logger.info(f"Found {len(mental_notes)} mental notes")
            return mental_notes

    def _format_response(
        self,
        mental_notes: list,
        validated: Dict[str, Any],
        context: ToolContext
    ) -> ToolResult:
        """Format query results into ToolResult

        Args:
            mental_notes: List of mental note models
            validated: Validated arguments
            context: Execution context

        Returns:
            ToolResult with formatted data
        """
        response_data = self.formatter.create_response_data(
            notes=mental_notes,
            session_id=validated["session_id"],
            mental_note_id=validated["mental_note_id"],
            limit=validated["limit"],
            user_id=validated["user_id"],
            project_id=validated["project_id"]
        )

        return ToolResult(success=True, data=response_data)
