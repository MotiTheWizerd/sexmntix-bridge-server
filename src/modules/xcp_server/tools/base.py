"""
Base Tool Interface for XCP Server

Abstract base class for all MCP tools, providing a consistent interface
for tool registration, validation, and execution.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from src.modules.core.event_bus.event_bus import EventBus
from src.modules.core.telemetry.logger import Logger
from src.modules.xcp_server.models.config import ToolContext
from src.modules.xcp_server.exceptions import XCPToolValidationError, XCPToolExecutionError
from src.events.schemas import EventType


class ToolParameter(BaseModel):
    """Definition of a tool parameter"""
    name: str = Field(description="Parameter name")
    type: str = Field(description="Parameter type (string, number, boolean, object, array)")
    description: str = Field(description="Human-readable parameter description")
    required: bool = Field(default=False, description="Whether this parameter is required")
    default: Optional[Any] = Field(default=None, description="Default value if not provided")
    enum: Optional[List[Any]] = Field(default=None, description="List of allowed values")


class ToolDefinition(BaseModel):
    """MCP tool definition"""
    name: str = Field(description="Unique tool identifier")
    description: str = Field(description="Human-readable tool description")
    parameters: List[ToolParameter] = Field(default_factory=list, description="Tool parameters")

    def to_mcp_schema(self) -> Dict[str, Any]:
        """Convert to MCP tool schema format"""
        properties = {}
        required = []

        for param in self.parameters:
            param_schema = {
                "type": param.type,
                "description": param.description
            }

            if param.enum:
                param_schema["enum"] = param.enum

            if param.default is not None:
                param_schema["default"] = param.default

            properties[param.name] = param_schema

            if param.required:
                required.append(param.name)

        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }


class ToolResult(BaseModel):
    """Result of tool execution"""
    success: bool = Field(description="Whether execution was successful")
    data: Any = Field(default=None, description="Result data")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    error_code: Optional[str] = Field(default=None, description="Error code if failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class BaseTool(ABC):
    """Abstract base class for all MCP tools

    All tools must implement:
    - get_definition(): Returns tool definition for MCP registration
    - execute(): Implements the tool's core logic
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

    @property
    def definition(self) -> ToolDefinition:
        """Get cached tool definition"""
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

    def validate_arguments(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Validate arguments against tool schema

        Args:
            arguments: Raw arguments from MCP client

        Returns:
            Dict[str, Any]: Validated arguments with defaults applied

        Raises:
            XCPToolValidationError: If validation fails
        """
        validated = {}
        definition = self.definition

        # Check required parameters
        for param in definition.parameters:
            if param.required and param.name not in arguments:
                raise XCPToolValidationError(
                    tool_name=definition.name,
                    message=f"Required parameter '{param.name}' is missing"
                )

            # Apply defaults
            if param.name not in arguments and param.default is not None:
                validated[param.name] = param.default
            elif param.name in arguments:
                validated[param.name] = arguments[param.name]

                # Validate enum
                if param.enum and validated[param.name] not in param.enum:
                    raise XCPToolValidationError(
                        tool_name=definition.name,
                        message=f"Parameter '{param.name}' must be one of {param.enum}"
                    )

        return validated

    async def run(
        self,
        context: ToolContext,
        arguments: Dict[str, Any]
    ) -> ToolResult:
        """Run tool with validation and event publishing

        Args:
            context: Execution context
            arguments: Tool arguments

        Returns:
            ToolResult: Execution result
        """
        tool_name = self.definition.name
        start_time = datetime.utcnow()

        try:
            # Validate arguments
            validated_args = self.validate_arguments(arguments)

            # Publish tool called event
            self.event_bus.publish(
                EventType.XCP_TOOL_CALLED.value,
                {
                    "tool_name": tool_name,
                    "user_id": context.user_id,
                    "project_id": context.project_id,
                    "arguments": validated_args,
                    "session_id": context.session_id
                }
            )

            self.logger.info(
                f"Executing tool '{tool_name}'",
                extra={
                    "tool_name": tool_name,
                    "user_id": context.user_id,
                    "project_id": context.project_id
                }
            )

            # Execute tool
            result = await self.execute(context, validated_args)

            # Calculate duration
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

            # Publish completion event
            if result.success:
                self.event_bus.publish(
                    EventType.XCP_TOOL_COMPLETED.value,
                    {
                        "tool_name": tool_name,
                        "user_id": context.user_id,
                        "project_id": context.project_id,
                        "result": result.data,
                        "duration_ms": duration_ms,
                        "session_id": context.session_id
                    }
                )

                self.logger.info(
                    f"Tool '{tool_name}' completed successfully",
                    extra={"duration_ms": duration_ms}
                )
            else:
                self.event_bus.publish(
                    EventType.XCP_TOOL_FAILED.value,
                    {
                        "tool_name": tool_name,
                        "user_id": context.user_id,
                        "project_id": context.project_id,
                        "error_message": result.error,
                        "error_code": result.error_code,
                        "session_id": context.session_id
                    }
                )

                self.logger.error(
                    f"Tool '{tool_name}' failed",
                    extra={"error": result.error, "error_code": result.error_code}
                )

            return result

        except XCPToolValidationError as e:
            self.logger.error(f"Tool validation failed: {e.message}")
            return ToolResult(
                success=False,
                error=e.message,
                error_code=e.code
            )

        except Exception as e:
            self.logger.exception(f"Tool execution failed: {str(e)}")

            self.event_bus.publish(
                EventType.XCP_TOOL_FAILED.value,
                {
                    "tool_name": tool_name,
                    "user_id": context.user_id,
                    "project_id": context.project_id,
                    "error_message": str(e),
                    "error_code": "UNEXPECTED_ERROR",
                    "session_id": context.session_id
                }
            )

            return ToolResult(
                success=False,
                error=f"Unexpected error: {str(e)}",
                error_code="UNEXPECTED_ERROR"
            )
