"""Tool Registry - Manages registered MCP tools"""

from typing import List
from src.modules.xcp_server.tools import BaseTool


class ToolRegistry:
    """Registry for storing and managing MCP tools"""

    def __init__(self):
        """Initialize an empty tool registry"""
        self._tools: List[BaseTool] = []

    def register(self, tool: BaseTool) -> None:
        """Register a tool in the registry

        Args:
            tool: The tool to register
        """
        self._tools.append(tool)

    def register_many(self, tools: List[BaseTool]) -> None:
        """Register multiple tools at once

        Args:
            tools: List of tools to register
        """
        self._tools.extend(tools)

    def get_all(self) -> List[BaseTool]:
        """Get all registered tools

        Returns:
            List of all registered tools
        """
        return self._tools.copy()

    def get_tool_names(self) -> List[str]:
        """Get names of all registered tools

        Returns:
            List of tool names
        """
        return [tool.definition.name for tool in self._tools]

    def count(self) -> int:
        """Get count of registered tools

        Returns:
            Number of registered tools
        """
        return len(self._tools)

    def clear(self) -> None:
        """Clear all registered tools"""
        self._tools.clear()
