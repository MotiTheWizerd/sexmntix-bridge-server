"""
Store Memory Tool Configuration

Tool definition, parameter schemas, and constants for the store_memory tool.
"""

from typing import List
from src.modules.xcp_server.tools.base import ToolDefinition, ToolParameter


class StoreMemoryConfig:
    """Configuration and tool definition for store_memory tool"""

    # Constants
    TOOL_NAME = "store_memory"
    TOOL_DESCRIPTION = (
        "Store a new memory log in the system. The memory will be automatically "
        "indexed for semantic search. Useful for saving important information, "
        "learnings, solutions, or context for future reference."
    )

    MAX_TAGS = 5
    DEFAULT_AGENT = "mcp_client"

    @classmethod
    def get_tool_definition(cls) -> ToolDefinition:
        """Get the complete tool definition for MCP registration

        Returns:
            ToolDefinition: Tool metadata and parameter schema
        """
        return ToolDefinition(
            name=cls.TOOL_NAME,
            description=cls.TOOL_DESCRIPTION,
            parameters=cls._get_parameters()
        )

    @classmethod
    def _get_parameters(cls) -> List[ToolParameter]:
        """Define all tool parameters

        Returns:
            List[ToolParameter]: List of parameter definitions
        """
        return [
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
                default=cls.DEFAULT_AGENT
            ),
            ToolParameter(
                name="tags",
                type="array",
                description=f"Optional tags for categorizing the memory (max {cls.MAX_TAGS} tags)",
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
