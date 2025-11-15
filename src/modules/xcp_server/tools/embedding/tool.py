"""
Embedding Tool - MCP Tool for generating text embeddings

Main tool implementation that orchestrates validation, generation, and formatting.
"""

from typing import Dict, Any

from src.modules.xcp_server.tools.base import BaseTool, ToolDefinition, ToolResult
from src.modules.xcp_server.models.config import ToolContext
from src.modules.xcp_server.exceptions import XCPToolExecutionError
from src.modules.core import EventBus, Logger
from src.modules.embeddings import EmbeddingService

from .config import EmbeddingToolConfig
from .validators import EmbeddingArgumentValidator
from .formatters import EmbeddingResultFormatter


class EmbeddingTool(BaseTool):
    """Tool for generating text embeddings

    This tool allows AI assistants to generate vector embeddings for text.
    Embeddings are useful for semantic similarity, clustering, and other
    vector-based operations. Results are cached for efficiency.

    The tool is organized into separate components:
    - config: Tool definition and parameter schemas
    - validators: Argument validation and sanitization
    - formatters: Result formatting and structuring
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
        self.config = EmbeddingToolConfig()
        self.validator = EmbeddingArgumentValidator()
        self.formatter = EmbeddingResultFormatter()

    def get_definition(self) -> ToolDefinition:
        """Get tool definition for MCP registration

        Returns:
            ToolDefinition: Tool metadata and parameter schema
        """
        return self.config.get_tool_definition()

    async def execute(
        self,
        context: ToolContext,
        arguments: Dict[str, Any]
    ) -> ToolResult:
        """Execute embedding generation

        Args:
            context: Execution context
            arguments: Tool arguments containing text and options

        Returns:
            ToolResult: Embedding vector and metadata
        """
        try:
            # Validate and extract arguments
            validated_args = self._validate_arguments(arguments)

            # Log generation request
            self._log_generation_request(validated_args, context)

            # Generate embedding
            embedding_result = await self._generate_embedding(validated_args)

            # Log generation success
            self._log_generation_success(embedding_result)

            # Format and return result
            return self._format_response(
                validated_args=validated_args,
                embedding_result=embedding_result,
                context=context
            )

        except ValueError as e:
            # Validation errors
            return ToolResult(
                success=False,
                error=str(e),
                error_code="INVALID_TEXT"
            )
        except Exception as e:
            # Unexpected errors
            self.logger.exception(f"Embedding generation failed: {str(e)}")
            raise XCPToolExecutionError(
                tool_name=self.config.TOOL_NAME,
                message=f"Failed to generate embedding: {str(e)}",
                original_error=e
            )

    def _validate_arguments(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and extract arguments using validator

        Args:
            arguments: Raw tool arguments

        Returns:
            Dictionary of validated arguments

        Raises:
            ValueError: If validation fails
        """
        return self.validator.extract_and_validate(arguments)

    def _log_generation_request(
        self,
        validated_args: Dict[str, Any],
        context: ToolContext
    ) -> None:
        """Log embedding generation request

        Args:
            validated_args: Validated arguments
            context: Execution context
        """
        self.logger.info(
            "Generating embedding",
            extra={
                "text_length": len(validated_args["text"]),
                "user_id": context.user_id,
                "project_id": context.project_id
            }
        )

    async def _generate_embedding(self, validated_args: Dict[str, Any]) -> Any:
        """Generate embedding using embedding service

        Args:
            validated_args: Validated arguments with text

        Returns:
            Embedding result from service
        """
        return await self.embedding_service.generate_embedding(
            text=validated_args["text"]
        )

    def _log_generation_success(self, embedding_result: Any) -> None:
        """Log successful embedding generation

        Args:
            embedding_result: Result from embedding service
        """
        self.logger.info(
            "Embedding generated successfully",
            extra={
                "dimensions": embedding_result.dimensions,
                "provider": embedding_result.provider,
                "cached": embedding_result.cached
            }
        )

    def _format_response(
        self,
        validated_args: Dict[str, Any],
        embedding_result: Any,
        context: ToolContext
    ) -> ToolResult:
        """Format embedding result into a ToolResult

        Args:
            validated_args: Validated arguments
            embedding_result: Result from embedding service
            context: Execution context

        Returns:
            ToolResult with formatted data
        """
        # Format embedding result
        response_data = self.formatter.format_embedding_result(
            text=validated_args["text"],
            embedding_result=embedding_result,
            return_full_vector=validated_args["return_full_vector"]
        )

        # Create response metadata
        response_metadata = self.formatter.create_response_metadata(
            user_id=context.user_id,
            project_id=context.project_id
        )

        return ToolResult(
            success=True,
            data=response_data,
            metadata=response_metadata
        )
