"""
Base Tool Interface - Simplified

Abstract base class for all MCP tools.
Simplified by delegating orchestration to ToolExecutor and telemetry to ToolTelemetry.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from src.modules.core.event_bus.event_bus import EventBus
from src.modules.core.telemetry.logger import Logger
from src.modules.xcp_server.models.config import ToolContext
from src.modules.xcp_server.tools.base.models import ToolDefinition, ToolResult
from src.modules.xcp_server.tools.base.execution import ToolExecutor
from src.modules.xcp_server.tools.base.telemetry import ToolTelemetry


class BaseTool(ABC):
    """Abstract base class for all MCP tools

    All tools must implement:
    - get_definition(): Returns tool definition for MCP registration
    - execute(): Implements the tool's core logic

    The base class handles validation, event publishing, and error handling
    through delegation to specialized components.
    """

    def __init__(
        self,
        event_bus: EventBus,
        logger: Logger
    ):
        """Initialize base tool

        Args:
            event_bus: Event bus for publishing events
            logger: Logger instance
        """
        self.event_bus = event_bus
        self.logger = logger
        self._definition: Optional[ToolDefinition] = None

        # Initialize orchestration components
        self._telemetry = ToolTelemetry(event_bus, logger)
        self._executor = ToolExecutor(self._telemetry)

    @property
    def definition(self) -> ToolDefinition:
        """Get cached tool definition

        Returns:
            ToolDefinition: Tool metadata and parameter schema
        """
        if self._definition is None:
            self._definition = self.get_definition()
        return self._definition

    @abstractmethod
    def get_definition(self) -> ToolDefinition:
        """Get tool definition for MCP registration

        Returns:
            ToolDefinition: Tool metadata and parameter schema
        """
        pass

    @abstractmethod
    async def execute(
        self,
        context: ToolContext,
        arguments: Dict[str, Any]
    ) -> ToolResult:
        """Execute the tool with given arguments

        Args:
            context: Execution context (user_id, project_id, etc.)
            arguments: Tool arguments validated against schema

        Returns:
            ToolResult: Execution result

        Raises:
            XCPToolExecutionError: If execution fails
        """
        pass

    async def run(
        self,
        context: ToolContext,
        arguments: Dict[str, Any]
    ) -> ToolResult:
        """Run tool with validation and event publishing

        This method orchestrates the complete execution flow by delegating
        to ToolExecutor, which handles:
        - Argument validation
        - Event publishing
        - Logging
        - Error handling

        Args:
            context: Execution context
            arguments: Tool arguments

        Returns:
            ToolResult: Execution result
        """
        return await self._executor.execute_with_telemetry(
            tool_name=self.definition.name,
            tool_definition=self.definition,
            context=context,
            arguments=arguments,
            execute_fn=self.execute
        )
