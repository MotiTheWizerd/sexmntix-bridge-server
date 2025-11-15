"""
Response Formatter

Formats tool execution results into MCP TextContent responses.
"""

import json
from typing import List
from mcp.types import TextContent

from src.modules.xcp_server.tools import ToolResult


class ResponseFormatter:
    """Formats tool results into MCP protocol responses

    This class handles the conversion of internal ToolResult objects
    into MCP TextContent responses that can be sent to MCP clients.
    """

    @staticmethod
    def format_success(result: ToolResult) -> List[TextContent]:
        """Format a successful tool result

        Args:
            result: Successful ToolResult with data

        Returns:
            List containing single TextContent with JSON-formatted data
        """
        response_text = json.dumps(result.data, indent=2, default=str)
        return [TextContent(type="text", text=response_text)]

    @staticmethod
    def format_error(result: ToolResult) -> List[TextContent]:
        """Format a failed tool result

        Args:
            result: Failed ToolResult with error message

        Returns:
            List containing single TextContent with error message
        """
        error_text = f"Tool execution failed: {result.error}"
        if result.error_code:
            error_text = f"[{result.error_code}] {error_text}"
        return [TextContent(type="text", text=error_text)]

    @staticmethod
    def format_exception(tool_name: str, error_message: str) -> List[TextContent]:
        """Format an exception message

        Args:
            tool_name: Name of the tool that raised the exception
            error_message: Error message from the exception

        Returns:
            List containing single TextContent with formatted error
        """
        return [TextContent(
            type="text",
            text=f"Error executing tool '{tool_name}': {error_message}"
        )]

    @staticmethod
    def format_tool_not_found(tool_name: str) -> List[TextContent]:
        """Format a tool not found error

        Args:
            tool_name: Name of the tool that was not found

        Returns:
            List containing single TextContent with error message
        """
        return [TextContent(
            type="text",
            text=f"Error: Tool '{tool_name}' not found"
        )]
