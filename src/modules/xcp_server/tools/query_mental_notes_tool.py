"""
Query Mental Notes Tool - MCP Tool for querying mental notes

Enables AI assistants to query and retrieve mental notes by session ID or other criteria.
"""

from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.xcp_server.tools.base import BaseTool, ToolDefinition, ToolParameter, ToolResult
from src.modules.xcp_server.models.config import ToolContext
from src.modules.xcp_server.exceptions import XCPToolExecutionError
from src.modules.core import EventBus, Logger
from src.database.repositories.mental_note_repository import MentalNoteRepository


class QueryMentalNotesTool(BaseTool):
    """Tool for querying mental notes

    This tool allows AI assistants to retrieve mental notes by session ID
    or get all notes within a limit. Useful for reviewing context, decisions,
    or insights from previous interactions.
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

    def get_definition(self) -> ToolDefinition:
        """Get tool definition for MCP registration

        Returns:
            ToolDefinition: Tool metadata and parameter schema
        """
        return ToolDefinition(
            name="query_mental_notes",
            description=(
                "Query and retrieve mental notes. You can search by session ID to get "
                "all notes from a specific session, or retrieve recent notes across all "
                "sessions. Useful for reviewing context, tracking conversation history, "
                "or understanding past decisions."
            ),
            parameters=[
                ToolParameter(
                    name="session_id",
                    type="string",
                    description="Optional session ID to filter notes from a specific session",
                    required=False
                ),
                ToolParameter(
                    name="mental_note_id",
                    type="number",
                    description="Optional specific mental note ID to retrieve",
                    required=False
                ),
                ToolParameter(
                    name="limit",
                    type="number",
                    description="Maximum number of notes to return (default: 50, max: 200)",
                    required=False,
                    default=50
                )
            ]
        )

    async def execute(
        self,
        context: ToolContext,
        arguments: Dict[str, Any]
    ) -> ToolResult:
        """Execute mental notes query

        Args:
            context: Execution context
            arguments: Validated arguments containing session_id, limit, etc.

        Returns:
            ToolResult: List of mental notes matching the criteria
        """
        try:
            # Extract arguments
            session_id = arguments.get("session_id")
            mental_note_id = arguments.get("mental_note_id")
            limit = min(int(arguments.get("limit", 50)), 200)  # Cap at 200

            self.logger.info(
                f"Querying mental notes",
                extra={
                    "session_id": session_id,
                    "mental_note_id": mental_note_id,
                    "limit": limit,
                    "user_id": context.user_id,
                    "project_id": context.project_id
                }
            )

            # Create database session and query mental notes
            async with self.db_session_factory() as db_session:
                repo = MentalNoteRepository(db_session)

                mental_notes = []

                # Query by specific ID
                if mental_note_id:
                    note = await repo.get_by_id(int(mental_note_id))
                    if note:
                        mental_notes = [note]

                # Query by session ID
                elif session_id:
                    mental_notes = await repo.get_by_session_id(session_id)
                    # Apply limit
                    mental_notes = mental_notes[:limit]

                # Get all recent notes
                else:
                    mental_notes = await repo.get_all(limit=limit)

                self.logger.info(f"Found {len(mental_notes)} mental notes")

                # Format results
                formatted_notes = []
                for note in mental_notes:
                    formatted_notes.append({
                        "id": note.id,
                        "session_id": note.session_id,
                        "start_time": note.start_time,
                        "content": note.raw_data.get("content", ""),
                        "note_type": note.raw_data.get("note_type", "note"),
                        "raw_data": note.raw_data,
                        "created_at": note.created_at.isoformat()
                    })

                return ToolResult(
                    success=True,
                    data={
                        "count": len(formatted_notes),
                        "mental_notes": formatted_notes,
                        "filters_applied": {
                            "session_id": session_id,
                            "mental_note_id": mental_note_id,
                            "limit": limit
                        }
                    },
                    metadata={
                        "user_id": context.user_id,
                        "project_id": context.project_id
                    }
                )

        except Exception as e:
            self.logger.exception(f"Mental notes query failed: {str(e)}")
            raise XCPToolExecutionError(
                tool_name="query_mental_notes",
                message=f"Failed to query mental notes: {str(e)}",
                original_error=e
            )
