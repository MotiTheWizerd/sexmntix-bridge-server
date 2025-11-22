"""
Configuration and schema definitions for embedding tool

Defines the tool's MCP interface, parameters, and metadata.
"""

from src.modules.xcp_server.tools.base import ToolDefinition, ToolParameter


class EmbeddingToolConfig:
    """Configuration and schema for embedding generation tool"""

    # Tool metadata
    TOOL_NAME = "generate_embedding"
    TOOL_DESCRIPTION = (
        "Generate a vector embedding for the given text using the configured "
        "embedding model. Returns a high-dimensional vector representation that "
        "captures semantic meaning. Useful for similarity calculations, clustering, "
        "or feeding into other ML models. Results are automatically cached."
    )

    # Default values
    DEFAULT_RETURN_FULL_VECTOR = False

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
                name="text",
                type="string",
                description="The text to generate an embedding for. Should be non-empty and meaningful.",
                required=True
            ),
            ToolParameter(
                name="return_full_vector",
                type="boolean",
                description=(
                    "Whether to return the full embedding vector in the response "
                    f"(default: {cls.DEFAULT_RETURN_FULL_VECTOR}, returns dimensions and provider info only)"
                ),
                required=False,
                default=cls.DEFAULT_RETURN_FULL_VECTOR
            )
        ]
