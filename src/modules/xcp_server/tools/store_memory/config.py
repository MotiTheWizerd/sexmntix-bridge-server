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
        "learnings, solutions, or context for future reference.\n\n"
        "Required format:\n"
        "{\n"
        "  \"user_id\": <number> (required),\n"
        "  \"project_id\": <string> (required),\n"
        "  \"memory_log\": {\n"
        "    \"content\": <string> (optional),\n"
        "    \"task\": <string> (optional),\n"
        "    \"agent\": <string> (optional, default: 'mcp_client'),\n"
        "    \"tags\": [<string>] (optional, max 5),\n"
        "    \"metadata\": {<key>: <value>} (optional),\n"
        "    ...any additional fields (optional)\n"
        "  }\n"
        "}\n\n"
        "The system will automatically add a datetime field.\n"
        "All fields in memory_log are optional and you can add custom fields."
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
                name="user_id",
                type="string",
                description="User ID (UUID format) for memory isolation",
                required=True
            ),
            ToolParameter(
                name="project_id",
                type="string",
                description="Project ID for memory isolation",
                required=True
            ),
            ToolParameter(
                name="memory_log",
                type="object",
                description="Memory log data containing content, task, agent, tags, and metadata",
                required=True
            )
        ]
