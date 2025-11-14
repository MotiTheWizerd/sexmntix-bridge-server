"""
Store Mental Note Tool - MCP Tool for storing mental notes

Enables AI assistants to store mental notes, which are timestamped observations
or thoughts organized by session.
"""

from typing import Dict, Any
import time
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.xcp_server.tools.base import BaseTool, ToolDefinition, ToolParameter, ToolResult
from src.modules.xcp_server.models.config import ToolContext
from src.modules.xcp_server.exceptions import XCPToolExecutionError
from src.modules.core import EventBus, Logger
from src.database.repositories.mental_note_repository import MentalNoteRepository


class StoreMentalNoteTool(BaseTool):
    """Tool for storing mental notes

    This tool allows AI assistants to store mental notes - timestamped observations,
    thoughts, or reflections organized by session. Mental notes are useful for
    tracking conversation context, decisions, or insights within a session.
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

    def get_definition(self) -> ToolDefinition:
        """Get tool definition for MCP registration

        Returns:
            ToolDefinition: Tool metadata and parameter schema
        """
        return ToolDefinition(
            name="store_mental_note",
            description=(
                "Store a mental note - a timestamped observation, thought, or reflection. "
                "Mental notes are organized by session ID and can track context, decisions, "
                "or insights during a conversation or task. Useful for maintaining state "
                "and understanding conversation flow."
            ),
            parameters=[
                ToolParameter(
                    name="content",
                    type="string",
                    description="The content of the mental note",
                    required=True
                ),
                ToolParameter(
                    name="session_id",
                    type="string",
                    description="Session identifier to group related mental notes (defaults to context session_id if available)",
                    required=False
                ),
                ToolParameter(
                    name="note_type",
                    type="string",
                    description="Type or category of the note (e.g., 'observation', 'decision', 'insight', 'context')",
                    required=False,
                    default="note"
                ),
                ToolParameter(
                    name="metadata",
                    type="object",
                    description="Optional additional metadata as key-value pairs",
                    required=False
                )
            ]
        )

    async def execute(
        self,
        context: ToolContext,
        arguments: Dict[str, Any]
    ) -> ToolResult:
        """Execute mental note storage

        Args:
            context: Execution context
            arguments: Validated arguments containing content, session_id, etc.

        Returns:
            ToolResult: Storage result with mental note ID
        """
        try:
            # Extract arguments
            content = arguments["content"]
            session_id = arguments.get("session_id", context.session_id or f"mcp_session_{int(time.time())}")
            note_type = arguments.get("note_type", "note")
            metadata = arguments.get("metadata", {})

            # Validate content
            if not content or not content.strip():
                return ToolResult(
                    success=False,
                    error="Content cannot be empty",
                    error_code="INVALID_CONTENT"
                )

            # Build raw_data structure
            start_time = int(time.time() * 1000)  # Milliseconds timestamp
            raw_data = {
                "sessionId": session_id,
                "startTime": start_time,
                "content": content,
                "note_type": note_type,
                "user_id": context.user_id,
                "project_id": context.project_id
            }

            # Merge additional metadata
            if metadata and isinstance(metadata, dict):
                raw_data.update(metadata)

            self.logger.info(
                f"Storing mental note",
                extra={
                    "session_id": session_id,
                    "note_type": note_type,
                    "user_id": context.user_id,
                    "project_id": context.project_id
                }
            )

            # Create database session and store mental note
            async with self.db_session_factory() as db_session:
                repo = MentalNoteRepository(db_session)

                mental_note = await repo.create(
                    session_id=session_id,
                    start_time=start_time,
                    raw_data=raw_data
                )

                self.logger.info(f"Mental note stored with id: {mental_note.id}")

                # Emit event
                self.event_bus.publish(
                    "mental_note.created",
                    {
                        "id": mental_note.id,
                        "session_id": session_id,
                        "note_type": note_type
                    }
                )

                return ToolResult(
                    success=True,
                    data={
                        "mental_note_id": mental_note.id,
                        "session_id": session_id,
                        "content": content,
                        "note_type": note_type,
                        "start_time": start_time,
                        "created_at": mental_note.created_at.isoformat(),
                        "message": "Mental note stored successfully"
                    },
                    metadata={
                        "user_id": context.user_id,
                        "project_id": context.project_id
                    }
                )

        except Exception as e:
            self.logger.exception(f"Mental note storage failed: {str(e)}")
            raise XCPToolExecutionError(
                tool_name="store_mental_note",
                message=f"Failed to store mental note: {str(e)}",
                original_error=e
            )
