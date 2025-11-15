"""
Store Memory Tool - Main Implementation

Tool for storing memory logs with automatic vector embedding generation.
Orchestrates validation, data building, storage, and event publishing.
"""

from typing import Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.xcp_server.tools.base import BaseTool, ToolDefinition, ToolResult
from src.modules.xcp_server.models.config import ToolContext
from src.modules.xcp_server.exceptions import XCPToolExecutionError
from src.modules.core import EventBus, Logger
from src.database.repositories.memory_log_repository import MemoryLogRepository

from src.modules.xcp_server.tools.store_memory.config import StoreMemoryConfig
from src.modules.xcp_server.tools.store_memory.validators import MemoryArgumentValidator
from src.modules.xcp_server.tools.store_memory.builders import MemoryDataBuilder
from src.modules.xcp_server.tools.store_memory.formatters import MemoryResultFormatter


class StoreMemoryTool(BaseTool):
    """Tool for storing memory logs with automatic vector embedding

    This tool allows AI assistants to store new memories in the system.
    Memories are stored in PostgreSQL and automatically get vector embeddings
    generated for semantic search via an event-driven workflow.

    The tool follows a clean architecture with separated concerns:
    - Config: Tool definition and constants
    - Validators: Argument validation
    - Builders: Raw data structure building
    - Formatters: Response formatting
    - Tool: Orchestration of all components
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

        # Initialize components
        self.config = StoreMemoryConfig()
        self.validator = MemoryArgumentValidator()
        self.builder = MemoryDataBuilder()
        self.formatter = MemoryResultFormatter()

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
        """Execute memory storage

        This method orchestrates the complete storage workflow:
        1. Validate arguments
        2. Build raw_data structure
        3. Store in database
        4. Publish event for vector storage
        5. Format and return response

        Args:
            context: Execution context with user/project defaults
            arguments: Validated arguments containing content, task, etc.

        Returns:
            ToolResult: Storage result with memory ID
        """
        try:
            # Step 1: Validate and extract arguments
            validated_args = self._validate_arguments(arguments, context)

            # Step 2: Build raw_data structure
            raw_data = self._build_raw_data(validated_args)

            # Step 3: Log storage request
            self._log_storage_request(validated_args, raw_data)

            # Step 4: Store in database
            memory_log = await self._store_in_database(validated_args, raw_data)

            # Step 5: Publish event for async vector storage
            self._publish_storage_event(memory_log, validated_args, raw_data)

            # Step 6: Format and return success response
            return self._format_success_response(memory_log, validated_args)

        except ValueError as e:
            # Validation errors
            return self._handle_validation_error(e)

        except Exception as e:
            # Unexpected errors
            return self._handle_execution_error(e)

    # Private helper methods

    def _validate_arguments(
        self,
        arguments: Dict[str, Any],
        context: ToolContext
    ) -> Dict[str, Any]:
        """Validate and extract arguments using validator

        Args:
            arguments: Raw arguments from tool call
            context: Execution context

        Returns:
            Dict[str, Any]: Validated arguments

        Raises:
            ValueError: If validation fails
        """
        return self.validator.extract_and_validate(arguments, context)

    def _build_raw_data(self, validated_args: Dict[str, Any]) -> Dict[str, Any]:
        """Build raw_data structure using builder

        Args:
            validated_args: Validated arguments

        Returns:
            Dict[str, Any]: Complete raw_data structure
        """
        return self.builder.build_raw_data(
            task=validated_args["task"],
            agent=validated_args["agent"],
            content=validated_args["content"],
            user_id=validated_args["user_id"],
            project_id=validated_args["project_id"],
            tags=validated_args["tags"],
            metadata=validated_args["metadata"]
        )

    def _log_storage_request(
        self,
        validated_args: Dict[str, Any],
        raw_data: Dict[str, Any]
    ) -> None:
        """Log memory storage request

        Args:
            validated_args: Validated arguments
            raw_data: Built raw_data structure
        """
        content = validated_args["content"]
        content_preview = content[:100] + "..." if len(content) > 100 else content

        self.logger.info(
            f"[STORE_MEMORY] Storing memory with content: {content_preview}",
            extra={
                "task": validated_args["task"],
                "user_id": validated_args["user_id"],
                "project_id": validated_args["project_id"],
                "has_content": bool(content),
                "raw_data_keys": list(raw_data.keys())
            }
        )

    async def _store_in_database(
        self,
        validated_args: Dict[str, Any],
        raw_data: Dict[str, Any]
    ):
        """Store memory in database

        Args:
            validated_args: Validated arguments
            raw_data: Built raw_data structure

        Returns:
            MemoryLog: Stored memory log object
        """
        async with self.db_session_factory() as db_session:
            repo = MemoryLogRepository(db_session)

            memory_log = await repo.create(
                task=validated_args["task"],
                agent=validated_args["agent"],
                date=datetime.utcnow(),
                raw_data=raw_data,
                user_id=validated_args["user_id"],
                project_id=validated_args["project_id"]
            )

            self.logger.info(f"Memory log stored with id: {memory_log.id}")

            return memory_log

    def _publish_storage_event(
        self,
        memory_log,
        validated_args: Dict[str, Any],
        raw_data: Dict[str, Any]
    ) -> None:
        """Publish memory_log.stored event for async vector storage

        Args:
            memory_log: Stored memory log object
            validated_args: Validated arguments
            raw_data: Built raw_data structure
        """
        event_data = self.formatter.create_event_data(
            memory_log=memory_log,
            task=validated_args["task"],
            agent=validated_args["agent"],
            raw_data=raw_data,
            user_id=validated_args["user_id"],
            project_id=validated_args["project_id"]
        )

        self.logger.info(
            f"[STORE_MEMORY] Publishing memory_log.stored event with data: {list(event_data.keys())}"
        )

        self.event_bus.publish("memory_log.stored", event_data)

        self.logger.info(
            f"[STORE_MEMORY] Memory stored successfully, vector storage scheduled (id: {memory_log.id})"
        )

    def _format_success_response(
        self,
        memory_log,
        validated_args: Dict[str, Any]
    ) -> ToolResult:
        """Format success response using formatter

        Args:
            memory_log: Stored memory log object
            validated_args: Validated arguments

        Returns:
            ToolResult: Success result with formatted data
        """
        response_data = self.formatter.format_success_response(
            memory_log=memory_log,
            task=validated_args["task"],
            content=validated_args["content"],
            user_id=validated_args["user_id"],
            project_id=validated_args["project_id"]
        )

        return ToolResult(
            success=True,
            data=response_data["data"],
            metadata=response_data["metadata"]
        )

    def _handle_validation_error(self, error: ValueError) -> ToolResult:
        """Handle validation errors

        Args:
            error: Validation error

        Returns:
            ToolResult: Error result
        """
        self.logger.error(f"Memory validation failed: {str(error)}")
        return ToolResult(
            success=False,
            error=str(error),
            error_code="VALIDATION_ERROR"
        )

    def _handle_execution_error(self, error: Exception) -> ToolResult:
        """Handle unexpected execution errors

        Args:
            error: Execution error

        Raises:
            XCPToolExecutionError: Wrapped execution error
        """
        self.logger.exception(f"Memory storage failed: {str(error)}")
        raise XCPToolExecutionError(
            tool_name="store_memory",
            message=f"Failed to store memory: {str(error)}",
            original_error=error
        )
