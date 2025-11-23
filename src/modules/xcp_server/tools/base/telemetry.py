"""
Tool telemetry - events and logging

Handles event publishing and logging for tool execution lifecycle.
Extracted from BaseTool to decouple telemetry concerns.
"""

from typing import Dict, Any

from src.modules.core.event_bus.event_bus import EventBus
from src.modules.core.telemetry.logger import Logger
from src.modules.xcp_server.models.config import ToolContext
from src.modules.xcp_server.tools.base.models import ToolResult
from src.events.schemas import EventType


class ToolTelemetry:
    """Handles event publishing and logging for tool execution"""

    def __init__(self, event_bus: EventBus, logger: Logger):
        """Initialize telemetry

        Args:
            event_bus: Event bus for publishing events
            logger: Logger instance
        """
        self.event_bus = event_bus
        self.logger = logger

    def log_execution_start(
        self,
        tool_name: str,
        context: ToolContext,
        arguments: Dict[str, Any]
    ) -> None:
        """Log and publish events for tool execution start

        Args:
            tool_name: Name of the tool being executed
            context: Execution context
            arguments: Validated arguments
        """
        # Publish tool called event
        self.event_bus.publish(
            EventType.XCP_TOOL_CALLED.value,
            {
                "tool_name": tool_name,
                "user_id": arguments.get("user_id"),
                "project_id": arguments.get("project_id"),
                "arguments": arguments,
                "session_id": context.session_id
            }
        )

        # Log execution start
        self.logger.info(
            f"Executing tool '{tool_name}'",
            extra={
                "tool_name": tool_name,
                "user_id": arguments.get("user_id"),
                "project_id": arguments.get("project_id")
            }
        )

    def log_execution_success(
        self,
        tool_name: str,
        context: ToolContext,
        result: ToolResult,
        duration_ms: float,
        arguments: Dict[str, Any] = None
    ) -> None:
        """Log and publish events for successful execution

        Args:
            tool_name: Name of the tool
            context: Execution context
            result: Tool execution result
            duration_ms: Execution duration in milliseconds
            arguments: Tool arguments (for extracting user_id/project_id)
        """
        # Log result data type before publishing
        self.logger.info(f"[TELEMETRY] Publishing result.data type: {type(result.data)}")

        # Publish completion event
        self.event_bus.publish(
            EventType.XCP_TOOL_COMPLETED.value,
            {
                "tool_name": tool_name,
                "user_id": arguments.get("user_id") if arguments else None,
                "project_id": arguments.get("project_id") if arguments else None,
                "result": result.data,
                "duration_ms": duration_ms,
                "session_id": context.session_id
            }
        )

        # Log success
        self.logger.info(
            f"Tool '{tool_name}' completed successfully",
            extra={"duration_ms": duration_ms}
        )

    def log_execution_failure(
        self,
        tool_name: str,
        context: ToolContext,
        result: ToolResult,
        arguments: Dict[str, Any] = None
    ) -> None:
        """Log and publish events for failed execution

        Args:
            tool_name: Name of the tool
            context: Execution context
            result: Tool execution result with error details
            arguments: Tool arguments (for extracting user_id/project_id)
        """
        # Publish failure event
        self.event_bus.publish(
            EventType.XCP_TOOL_FAILED.value,
            {
                "tool_name": tool_name,
                "user_id": arguments.get("user_id") if arguments else None,
                "project_id": arguments.get("project_id") if arguments else None,
                "error_message": result.error,
                "error_code": result.error_code,
                "session_id": context.session_id
            }
        )

        # Log failure
        self.logger.error(
            f"Tool '{tool_name}' failed",
            extra={"error": result.error, "error_code": result.error_code}
        )

    def log_validation_error(
        self,
        tool_name: str,
        error_message: str,
        error_code: str
    ) -> None:
        """Log validation errors

        Args:
            tool_name: Name of the tool
            error_message: Error message
            error_code: Error code
        """
        self.logger.error(f"Tool validation failed: {error_message}")

    def log_unexpected_error(
        self,
        tool_name: str,
        context: ToolContext,
        error: Exception,
        arguments: Dict[str, Any] = None
    ) -> None:
        """Log and publish events for unexpected errors

        Args:
            tool_name: Name of the tool
            context: Execution context
            error: Exception that occurred
            arguments: Tool arguments (for extracting user_id/project_id)
        """
        # Log exception with traceback
        self.logger.exception(f"Tool execution failed: {str(error)}")

        # Publish failure event
        self.event_bus.publish(
            EventType.XCP_TOOL_FAILED.value,
            {
                "tool_name": tool_name,
                "user_id": arguments.get("user_id") if arguments else None,
                "project_id": arguments.get("project_id") if arguments else None,
                "error_message": str(error),
                "error_code": "UNEXPECTED_ERROR",
                "session_id": context.session_id
            }
        )
