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
                        
      { "user_id": "string", "project_id": "string",
                         "session_id": "string", "task": "string",
                         "agent": "string", 
                        "memory_log": { "component": "string", "complexity": { "technical": "string", "business": "string", "coordination": "string" }, "files_modified": "string", "files_touched": [ "string" ], "tests_added": "string", "related_tasks": [ "string" ], "outcomes": { "performance_impact": "string", "test_coverage_delta": "string", "technical_debt_reduced": "string", "follow_up_needed": true }, "summary": "string", "root_cause": "string", "solution": { "approach": "string", "key_changes": [ "string" ] }, "validation": "string", "gotchas": [ { "issue": "string", "solution": "string", "category": "string", "severity": "string" } ], "lesson": "string", "tags": [ "string" ], "code_context": { "key_patterns": [ "string" ], "api_surface": [ "string" ], "dependencies_added": [ "string" ], "breaking_changes": [ "string" ] }, "future_planning": { "next_logical_steps": [ "string" ], "architecture_decisions": { "additionalProp1": "string", "additionalProp2": "string", "additionalProp3": "string" }, "extension_points": [ "string" ] }, "user_context": { "development_style": "string", "naming_preferences": "string", "architecture_philosophy": "string", "quality_standards": "string" }, "semantic_context": { "domain_concepts": [ "string" ], "technical_patterns": [ "string" ], "integration_points": [ "string" ] }, "content": "string", "metadata": {}, "additionalProp1": {} } 
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
