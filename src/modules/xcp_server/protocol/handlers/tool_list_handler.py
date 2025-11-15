"""
Tool List Handler

Handles the MCP list_tools() operation, converting internal tool definitions
to MCP Tool schema format.
"""

from typing import List
from mcp.types import Tool

from src.modules.core import Logger
from src.modules.xcp_server.tools import BaseTool


class ToolListHandler:
    """Handles tool listing for MCP clients

    This handler converts internal BaseTool definitions into MCP Tool
    schema format that clients can use to discover available tools.
    """

    def __init__(self, tools: List[BaseTool], logger: Logger):
        """Initialize tool list handler

        Args:
            tools: List of available tools
            logger: Logger instance
        """
        self.tools = tools
        self.logger = logger

    async def handle_list_tools(self) -> List[Tool]:
        """Handle list_tools() request from MCP client

        Converts all registered tools to MCP Tool schema format.

        Returns:
            List of MCP Tool instances with name, description, and input schema
        """
        self.logger.debug("MCP client requested tool list")

        mcp_tools = []
        for tool in self.tools:
            definition = tool.definition
            mcp_schema = definition.to_mcp_schema()

            # Convert to MCP Tool type
            mcp_tools.append(
                Tool(
                    name=mcp_schema["name"],
                    description=mcp_schema["description"],
                    inputSchema=mcp_schema["inputSchema"]
                )
            )

        self.logger.info(f"Returned {len(mcp_tools)} tools to MCP client")
        return mcp_tools
