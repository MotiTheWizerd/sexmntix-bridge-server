"""
Store Mental Note Tool Configuration

Defines tool metadata, parameters, and constants for the mental note storage tool.
"""

from src.modules.xcp_server.tools.base import ToolDefinition, ToolParameter


class StoreMentalNoteConfig:
    """Configuration for the store mental note tool

    Centralizes all tool metadata, parameter definitions, and constants.
    """

    # Tool identity
    TOOL_NAME = "store_mental_note"
    TOOL_DESCRIPTION = (
        "Store a mental note - a timestamped observation, thought, or reflection. "
        "Mental notes are organized by session ID and can track context, decisions, "
        "or insights during a conversation or task. Useful for maintaining state "
        "and understanding conversation flow."
    )

    # Default values
    DEFAULT_NOTE_TYPE = "note"

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
                name="query",
                type="string",
                description="semantic query to remember about something",
                required=True
            )
        ]
