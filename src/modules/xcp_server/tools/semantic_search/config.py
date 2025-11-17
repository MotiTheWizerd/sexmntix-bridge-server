"""
Configuration and schema definitions for semantic search tool

Defines the tool's MCP interface, parameters, and metadata.
"""

from src.modules.xcp_server.tools.base import ToolDefinition, ToolParameter


class SemanticSearchConfig:
    """Configuration and schema for semantic search tool"""

    # Tool metadata
    TOOL_NAME = "semantic_search"
    TOOL_DESCRIPTION = (
        "Search through stored memories using semantic similarity. "
        "Provide a natural language query and get back the most relevant memories. "
        "Useful for finding related information, past solutions, or similar contexts."
    )

    # Parameter constraints
    MAX_LIMIT = 50
    DEFAULT_LIMIT = 10
    DEFAULT_MIN_SIMILARITY = 0.0
    DEFAULT_HALF_LIFE_DAYS = 30
    DEFAULT_ENABLE_TEMPORAL_DECAY = False

    @classmethod
    def get_tool_definition(cls) -> ToolDefinition:
        """Get the complete tool definition for MCP registration

        Returns:
            ToolDefinition with all parameters and metadata
        """
        return ToolDefinition(
            name=cls.TOOL_NAME,
            description=cls.TOOL_DESCRIPTION,
            parameters=cls._get_parameters()
        )

    @classmethod
    def _get_parameters(cls) -> list[ToolParameter]:
        """Define all tool parameters

        Returns:
            List of ToolParameter definitions
        """
        return [
            ToolParameter(
                name="query",
                type="string",
                description=(
                    "The search query in natural language "
                    "(e.g., 'authentication bug fixes', 'database optimization tips')"
                ),
                required=True
            ),
            ToolParameter(
                name="limit",
                type="number",
                description=f"Maximum number of results to return (default: {cls.DEFAULT_LIMIT}, max: {cls.MAX_LIMIT})",
                required=False,
                default=cls.DEFAULT_LIMIT
            ),
            ToolParameter(
                name="min_similarity",
                type="number",
                description=(
                    "Minimum similarity score threshold from 0.0 to 1.0 "
                    f"(default: {cls.DEFAULT_MIN_SIMILARITY}). Higher values return more relevant results."
                ),
                required=False,
                default=cls.DEFAULT_MIN_SIMILARITY
            ),
            ToolParameter(
                name="user_id",
                type="string",
                description="User ID (UUID format) for memory isolation (required)",
                required=True
            ),
            ToolParameter(
                name="project_id",
                type="string",
                description="Project ID for memory isolation (required)",
                required=True
            ),
            ToolParameter(
                name="enable_temporal_decay",
                type="boolean",
                description=(
                    "Apply exponential decay based on memory age to boost recent memories "
                    f"(default: {cls.DEFAULT_ENABLE_TEMPORAL_DECAY})"
                ),
                required=False,
                default=cls.DEFAULT_ENABLE_TEMPORAL_DECAY
            ),
            ToolParameter(
                name="half_life_days",
                type="number",
                description=(
                    "Half-life in days for exponential decay. "
                    f"Memories lose 50% weight after this many days (default: {cls.DEFAULT_HALF_LIFE_DAYS})"
                ),
                required=False,
                default=cls.DEFAULT_HALF_LIFE_DAYS
            )
        ]
