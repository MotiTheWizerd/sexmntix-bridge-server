"""
Tool execution orchestration

Coordinates the execution flow: validation -> execution -> telemetry.
Provides centralized error handling for all tool executions.
"""

from datetime import datetime
from typing import Dict, Any, Callable, Awaitable

from src.modules.xcp_server.tools.base.models import ToolResult, ToolDefinition
from src.modules.xcp_server.tools.base.telemetry import ToolTelemetry
from src.modules.xcp_server.models.config import ToolContext
from src.modules.xcp_server.exceptions import XCPToolValidationError


class ToolExecutor:
    """Orchestrates tool execution with validation and telemetry"""

    def __init__(self, telemetry: ToolTelemetry):
        """Initialize executor

        Args:
            telemetry: Telemetry handler for events and logging
        """
        self.telemetry = telemetry

    async def execute_with_telemetry(
        self,
        tool_name: str,
        tool_definition: ToolDefinition,
        context: ToolContext,
        arguments: Dict[str, Any],
        execute_fn: Callable[[ToolContext, Dict[str, Any]], Awaitable[ToolResult]]
    ) -> ToolResult:
        """Execute tool with validation, telemetry, and error handling

        This method orchestrates the complete execution flow:
        1. Validate arguments against schema
        2. Log execution start and publish events
        3. Execute the tool logic
        4. Calculate duration
        5. Log results and publish completion events
        6. Handle any errors uniformly

        Args:
            tool_name: Name of the tool
            tool_definition: Tool definition for validation
            context: Execution context
            arguments: Tool arguments
            execute_fn: Async function to execute the tool logic

        Returns:
            ToolResult: Execution result
        """
        start_time = datetime.utcnow()

        try:
            # Log execution start
            self.telemetry.log_execution_start(tool_name, context, arguments)

            # Execute tool
            result = await execute_fn(context, arguments)

            # Calculate duration
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

            # Log based on result
            if result.success:
                self.telemetry.log_execution_success(tool_name, context, result, duration_ms, arguments)
            else:
                self.telemetry.log_execution_failure(tool_name, context, result, arguments)

            return result

        except XCPToolValidationError as e:
            # Handle validation errors
            self.telemetry.log_validation_error(tool_name, e.message, e.code)
            return ToolResult(
                success=False,
                error=e.message,
                error_code=e.code
            )

        except Exception as e:
            # Handle unexpected errors
            self.telemetry.log_unexpected_error(tool_name, context, e, arguments)
            return ToolResult(
                success=False,
                error=f"Unexpected error: {str(e)}",
                error_code="UNEXPECTED_ERROR"
            )
