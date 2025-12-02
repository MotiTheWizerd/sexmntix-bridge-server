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
    TOOL_DESCRIPTION = ("""
        Store a new memory log in the system. The memory will be automatically 
        indexed for semantic search. Useful for saving important information, 
        learnings, solutions, or context for future reference.\n\n
        The system will automatically add user_id, project_id, and datetime fields.\n
       All fields in memory_log are optional and you can add custom fields.
         USE EXACTLY THIS TEMPLATE:               
     {
        "user_id": "uuid-string",
        "project_id": "default",
        "session_id": "string",
        "task": "task-name-kebab-case",
        "agent": "claude-sonnet-4",
        "memory_log": {
            "component": "component-name",
            "complexity": {...},
            "outcomes": {...},
            "solution": {...},
            "gotchas": [...],
            "code_context": {...},
            "future_planning": {...},
            "user_context": {...},
            "semantic_context": {...},
            "tags": ["searchable", "keywords"],
            ... (all other fields optional)
        }
    }
                        """
         
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
                name="memory_log",
                type="object",
                description="Memory log data containing content, task, agent, tags, and metadata",
                required=True
            )
        ]
