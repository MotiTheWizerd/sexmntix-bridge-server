"""
Embedding Tool - MCP Tool for generating text embeddings

Enables AI assistants to generate vector embeddings for text using the configured
embedding provider (e.g., Google's text-embedding-004).
"""

from typing import Dict, Any
from src.modules.xcp_server.tools.base import BaseTool, ToolDefinition, ToolParameter, ToolResult
from src.modules.xcp_server.models.config import ToolContext
from src.modules.xcp_server.exceptions import XCPToolExecutionError
from src.modules.core import EventBus, Logger
from src.modules.embeddings import EmbeddingService


class EmbeddingTool(BaseTool):
    """Tool for generating text embeddings

    This tool allows AI assistants to generate vector embeddings for text.
    Embeddings are useful for semantic similarity, clustering, and other
    vector-based operations. Results are cached for efficiency.
    """

    def __init__(
        self,
        event_bus: EventBus,
        logger: Logger,
        embedding_service: EmbeddingService
    ):
        """Initialize embedding tool

        Args:
            event_bus: Event bus for publishing events
            logger: Logger instance
            embedding_service: Service for generating embeddings
        """
        super().__init__(event_bus, logger)
        self.embedding_service = embedding_service

    def get_definition(self) -> ToolDefinition:
        """Get tool definition for MCP registration

        Returns:
            ToolDefinition: Tool metadata and parameter schema
        """
        return ToolDefinition(
            name="generate_embedding",
            description=(
                "Generate a vector embedding for the given text using the configured "
                "embedding model. Returns a high-dimensional vector representation that "
                "captures semantic meaning. Useful for similarity calculations, clustering, "
                "or feeding into other ML models. Results are automatically cached."
            ),
            parameters=[
                ToolParameter(
                    name="text",
                    type="string",
                    description="The text to generate an embedding for. Should be non-empty and meaningful.",
                    required=True
                ),
                ToolParameter(
                    name="return_full_vector",
                    type="boolean",
                    description="Whether to return the full embedding vector in the response (default: false, returns dimensions and provider info only)",
                    required=False,
                    default=False
                )
            ]
        )

    async def execute(
        self,
        context: ToolContext,
        arguments: Dict[str, Any]
    ) -> ToolResult:
        """Execute embedding generation

        Args:
            context: Execution context
            arguments: Validated arguments containing text

        Returns:
            ToolResult: Embedding vector and metadata
        """
        try:
            text = arguments["text"]
            return_full_vector = arguments.get("return_full_vector", False)

            # Validate text
            if not text or not text.strip():
                return ToolResult(
                    success=False,
                    error="Text cannot be empty",
                    error_code="INVALID_TEXT"
                )

            self.logger.info(
                f"Generating embedding",
                extra={
                    "text_length": len(text),
                    "user_id": context.user_id,
                    "project_id": context.project_id
                }
            )

            # Generate embedding
            result = await self.embedding_service.generate_embedding(text=text)

            self.logger.info(
                f"Embedding generated successfully",
                extra={
                    "dimensions": result.dimensions,
                    "provider": result.provider,
                    "cached": result.cached
                }
            )

            # Build response data
            response_data = {
                "text": text,
                "model": result.model,
                "provider": result.provider,
                "dimensions": result.dimensions,
                "cached": result.cached,
                "metadata": {
                    "text_length": len(text),
                    "generation_time": result.metadata.get("generation_time_ms", 0)
                }
            }

            # Optionally include full vector
            if return_full_vector:
                response_data["embedding"] = result.embedding
                response_data["message"] = "Embedding vector generated successfully"
            else:
                # Provide sample of vector for verification
                response_data["embedding_sample"] = result.embedding[:5] if result.embedding else []
                response_data["message"] = (
                    "Embedding generated successfully. Use 'return_full_vector: true' "
                    "to get the complete vector."
                )

            return ToolResult(
                success=True,
                data=response_data,
                metadata={
                    "user_id": context.user_id,
                    "project_id": context.project_id
                }
            )

        except Exception as e:
            self.logger.exception(f"Embedding generation failed: {str(e)}")
            raise XCPToolExecutionError(
                tool_name="generate_embedding",
                message=f"Failed to generate embedding: {str(e)}",
                original_error=e
            )
