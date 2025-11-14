"""
Store Memory Tool - MCP Tool for storing new memory logs

Enables AI assistants to store new memories with automatic vector embedding generation.
"""

from typing import Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.xcp_server.tools.base import BaseTool, ToolDefinition, ToolParameter, ToolResult
from src.modules.xcp_server.models.config import ToolContext
from src.modules.xcp_server.exceptions import XCPToolExecutionError
from src.modules.core import EventBus, Logger
from src.database.repositories.memory_log_repository import MemoryLogRepository


class StoreMemoryTool(BaseTool):
    """Tool for storing memory logs with automatic vector embedding

    This tool allows AI assistants to store new memories in the system.
    Memories are stored in PostgreSQL and automatically get vector embeddings
    generated for semantic search via an event-driven workflow.
    """

    def __init__(
        self,
        event_bus: EventBus,
        logger: Logger,
        db_session_factory
    ):
        """Initialize store memory tool

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
            name="store_memory",
            description=(
                "Store a new memory log in the system. The memory will be automatically "
                "indexed for semantic search. Useful for saving important information, "
                "learnings, solutions, or context for future reference."
            ),
            parameters=[
                ToolParameter(
                    name="content",
                    type="string",
                    description="The main content/text of the memory to store",
                    required=True
                ),
                ToolParameter(
                    name="task",
                    type="string",
                    description="Task or category for this memory (e.g., 'bug_fix', 'learning', 'solution')",
                    required=True
                ),
                ToolParameter(
                    name="agent",
                    type="string",
                    description="Agent or source of this memory (e.g., 'claude', 'user', 'system')",
                    required=False,
                    default="mcp_client"
                ),
                ToolParameter(
                    name="tags",
                    type="array",
                    description="Optional tags for categorizing the memory (max 5 tags)",
                    required=False
                ),
                ToolParameter(
                    name="metadata",
                    type="object",
                    description="Optional additional metadata as key-value pairs",
                    required=False
                ),
                ToolParameter(
                    name="user_id",
                    type="number",
                    description="Override the default user ID for this memory (optional)",
                    required=False
                ),
                ToolParameter(
                    name="project_id",
                    type="string",
                    description="Override the default project ID for this memory (optional)",
                    required=False
                )
            ]
        )

    async def execute(
        self,
        context: ToolContext,
        arguments: Dict[str, Any]
    ) -> ToolResult:
        """Execute memory storage

        Args:
            context: Execution context with user/project defaults
            arguments: Validated arguments containing content, task, etc.

        Returns:
            ToolResult: Storage result with memory ID
        """
        try:
            # Extract arguments with context overrides
            content = arguments["content"]
            task = arguments["task"]
            agent = arguments.get("agent", "mcp_client")
            tags = arguments.get("tags", [])
            metadata = arguments.get("metadata", {})
            user_id = str(arguments.get("user_id", context.user_id))
            project_id = arguments.get("project_id", context.project_id)

            # Validate tags (max 5)
            if isinstance(tags, list) and len(tags) > 5:
                return ToolResult(
                    success=False,
                    error="Maximum of 5 tags allowed",
                    error_code="TOO_MANY_TAGS"
                )

            # Build raw_data structure
            raw_data = {
                "task": task,
                "agent": agent,
                "date": datetime.utcnow().isoformat(),
                "content": content,
                "user_id": user_id,
                "project_id": project_id
            }

            # Add tags to raw_data
            if tags and isinstance(tags, list):
                for i, tag in enumerate(tags[:5]):  # Max 5 tags
                    raw_data[f"tag_{i}"] = str(tag)

            # Merge additional metadata
            if metadata and isinstance(metadata, dict):
                raw_data.update(metadata)

            self.logger.info(
                f"Storing memory",
                extra={
                    "task": task,
                    "user_id": user_id,
                    "project_id": project_id
                }
            )

            # Create database session and store memory
            async with self.db_session_factory() as db_session:
                repo = MemoryLogRepository(db_session)

                memory_log = await repo.create(
                    task=task,
                    agent=agent,
                    date=datetime.utcnow(),
                    raw_data=raw_data,
                    user_id=user_id,
                    project_id=project_id
                )

                self.logger.info(f"Memory log stored with id: {memory_log.id}")

                # Emit event for async vector storage
                event_data = {
                    "memory_log_id": memory_log.id,
                    "task": task,
                    "agent": agent,
                    "date": memory_log.date,
                    "raw_data": raw_data,
                    "user_id": user_id,
                    "project_id": project_id,
                }

                self.event_bus.publish("memory_log.stored", event_data)

                self.logger.info(
                    f"Memory stored successfully, vector storage scheduled (id: {memory_log.id})"
                )

                return ToolResult(
                    success=True,
                    data={
                        "memory_id": memory_log.id,
                        "task": task,
                        "content": content,
                        "created_at": memory_log.created_at.isoformat(),
                        "message": "Memory stored successfully and will be indexed for semantic search"
                    },
                    metadata={
                        "user_id": user_id,
                        "project_id": project_id
                    }
                )

        except Exception as e:
            self.logger.exception(f"Memory storage failed: {str(e)}")
            raise XCPToolExecutionError(
                tool_name="store_memory",
                message=f"Failed to store memory: {str(e)}",
                original_error=e
            )
