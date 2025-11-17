"""
Query Mental Notes Tool Configuration

Defines tool metadata, parameters, and constants for the mental notes query tool.
"""

from src.modules.xcp_server.tools.base import ToolDefinition, ToolParameter


class QueryMentalNotesConfig:
    """Configuration for the query mental notes tool

    Centralizes all tool metadata, parameter definitions, and constants.
    """

    # Tool identity
    TOOL_NAME = "query_mental_notes"
    TOOL_DESCRIPTION = (
        "Query and retrieve mental notes. You can search by session ID to get "
        "all notes from a specific session, or retrieve recent notes across all "
        "sessions. Useful for reviewing context, tracking conversation history, "
        "or understanding past decisions."
    )

    # Limit constants
    DEFAULT_LIMIT = 50
    MAX_LIMIT = 200

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
        """Define tool parameters

        Returns:
            List of ToolParameter instances
        """
        return [
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
                name="session_id",
                type="string",
                description="Optional session ID to filter notes from a specific session",
                required=False
            ),
            ToolParameter(
                name="mental_note_id",
                type="number",
                description="Optional specific mental note ID to retrieve",
                required=False
            ),
            ToolParameter(
                name="limit",
                type="number",
                description=f"Maximum number of notes to return (default: {cls.DEFAULT_LIMIT}, max: {cls.MAX_LIMIT})",
                required=False,
                default=cls.DEFAULT_LIMIT
            )
        ]
