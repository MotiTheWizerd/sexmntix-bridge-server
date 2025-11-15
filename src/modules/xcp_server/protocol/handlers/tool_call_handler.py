"""
Tool Call Handler

Handles the MCP call_tool() operation, executing tools and formatting responses.
"""

from typing import Dict, List, Any
from mcp.types import TextContent

from src.modules.core import Logger
from src.modules.xcp_server.tools import BaseTool
from src.modules.xcp_server.exceptions import XCPToolExecutionError
from src.modules.xcp_server.protocol.utils import ResponseFormatter, ContextBuilder


class ToolCallHandler:
    """Handles tool execution for MCP clients

    This handler receives tool calls from MCP clients, executes the requested
    tool with the provided arguments, and formats the response appropriately.

    Note: The call_tool() handler is marked as "probably dead code" in the
    original implementation. This class preserves that functionality but
    maintains the comment for future investigation.
    """

    def __init__(
        self,
        tool_registry: Dict[str, BaseTool],
        context_builder: ContextBuilder,
        logger: Logger
    ):
        """Initialize tool call handler

        Args:
            tool_registry: Dictionary mapping tool names to BaseTool instances
            context_builder: Builder for creating ToolContext instances
            logger: Logger instance
        """
        self.tool_registry = tool_registry
        self.context_builder = context_builder
        self.logger = logger

    async def handle_call_tool(
        self,
        name: str,
        arguments: Dict[str, Any]
    ) -> List[TextContent]:
        """Handle call_tool() request from MCP client

        Args:
            name: Tool name to execute
            arguments: Tool arguments from client

        Returns:
            List of TextContent with tool results or error messages
        """
        self.logger.info(
            f"MCP tool call received",
            extra={"tool_name": name, "arguments": arguments}
        )

        # Get tool from registry
        tool = self.tool_registry.get(name)
        if not tool:
            self.logger.error(f"Tool '{name}' not found")
            return ResponseFormatter.format_tool_not_found(name)

        try:
            # Create execution context
            context = self.context_builder.build_default_context()

            # Execute tool
            result = await tool.run(context, arguments)

            # Format response based on result
            if result.success:
                return ResponseFormatter.format_success(result)
            else:
                return ResponseFormatter.format_error(result)

        except XCPToolExecutionError as e:
            error_msg = f"Tool execution error: {e.message}"
            self.logger.error(error_msg, extra={"error_code": e.code})
            return ResponseFormatter.format_exception(name, error_msg)

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self.logger.exception(f"Unexpected error executing tool '{name}': {str(e)}")
            return ResponseFormatter.format_exception(name, error_msg)
