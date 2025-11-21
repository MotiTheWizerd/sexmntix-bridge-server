"""
Semantic Search Tool - MCP Tool for searching memories using vector similarity

Main tool implementation that orchestrates validation, search, and formatting.
"""

from typing import Dict, Any

from src.modules.xcp_server.tools.base import BaseTool, ToolDefinition, ToolResult
from src.modules.xcp_server.models.config import ToolContext
from src.modules.xcp_server.exceptions import XCPToolExecutionError
from src.modules.core import EventBus, Logger
from src.modules.embeddings import EmbeddingService
from src.api.dependencies.vector_storage import create_vector_storage_service

from .config import SemanticSearchConfig
from .validators import SearchArgumentValidator
from .formatters import SearchResultFormatter


class SemanticSearchTool(BaseTool):
    """Tool for semantic search in memory logs using vector similarity

    This tool allows AI assistants to search through stored memories
    using natural language queries. It leverages vector embeddings
    to find semantically similar memories.

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
        """Initialize semantic search tool

        Args:
            event_bus: Event bus for publishing events
            logger: Logger instance
            embedding_service: Service for generating embeddings
        """
        super().__init__(event_bus, logger)
        self.embedding_service = embedding_service
        self.config = SemanticSearchConfig()
        self.validator = SearchArgumentValidator()
        self.formatter = SearchResultFormatter()

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
        """Execute semantic search

        Args:
            context: Execution context with user/project defaults
            arguments: Tool arguments containing query, limit, etc.

        Returns:
            ToolResult: Search results with similarity scores and metadata
        """
        try:
            # Validate and extract arguments
            validated_args = self._validate_arguments(arguments, context)

            # Log search execution
            self._log_search_execution(validated_args)

            # Perform search
            results = await self._perform_search(validated_args)

            # Format and return results
            return self._format_response(results, validated_args)

        except ValueError as e:
            # Validation errors
            return ToolResult(
                success=False,
                error=str(e),
                error_code="VALIDATION_ERROR"
            )
        except Exception as e:
            # Unexpected errors
            self.logger.exception(f"Semantic search failed: {str(e)}")
            raise XCPToolExecutionError(
                tool_name=self.config.TOOL_NAME,
                message=f"Search operation failed: {str(e)}",
                original_error=e
            )

    def _validate_arguments(
        self,
        arguments: Dict[str, Any],
        context: ToolContext
    ) -> Dict[str, Any]:
        """Validate and extract arguments using validator

        Args:
            arguments: Raw tool arguments
            context: Execution context with defaults

        Returns:
            Dictionary of validated arguments

        Raises:
            ValueError: If validation fails
        """
        return self.validator.extract_and_validate(
            arguments=arguments,
            context_user_id=None,
            context_project_id=None
        )

    def _log_search_execution(self, validated_args: Dict[str, Any]) -> None:
        """Log search execution details

        Args:
            validated_args: Validated search arguments
        """
        self.logger.info(
            "Executing semantic search",
            extra={
                "query": validated_args["query"],
                "user_id": validated_args["user_id"],
                "project_id": validated_args["project_id"],
                "limit": validated_args["limit"],
                "min_similarity": validated_args["min_similarity"],
                "enable_temporal_decay": validated_args["enable_temporal_decay"],
                "half_life_days": validated_args["half_life_days"]
            }
        )

    async def _perform_search(self, validated_args: Dict[str, Any]) -> list:
        """Perform the actual semantic search

        Args:
            validated_args: Validated search arguments

        Returns:
            List of raw search results from vector storage
        """
        # Create per-user/project vector storage service
        vector_service = create_vector_storage_service(
            user_id=validated_args["user_id"],
            project_id=validated_args["project_id"],
            embedding_service=self.embedding_service,
            event_bus=self.event_bus,
            logger=self.logger
        )

        # Perform semantic search
        return await vector_service.search_similar_memories(
            query=validated_args["query"],
            user_id=validated_args["user_id"],
            project_id=validated_args["project_id"],
            limit=validated_args["limit"],
            min_similarity=validated_args["min_similarity"],
            enable_temporal_decay=validated_args["enable_temporal_decay"],
            half_life_days=validated_args["half_life_days"]
        )

    def _format_response(
        self,
        results: list,
        validated_args: Dict[str, Any]
    ) -> ToolResult:
        """Format search results into a ToolResult

        Args:
            results: Raw search results from vector storage
            validated_args: Validated search arguments

        Returns:
            ToolResult with formatted data
        """
        # Format individual results
        formatted_results = self.formatter.format_search_results(results)

        # Create complete response structure
        response_data = self.formatter.create_response_data(
            query=validated_args["query"],
            formatted_results=formatted_results,
            min_similarity=validated_args["min_similarity"],
            limit=validated_args["limit"],
            user_id=validated_args["user_id"],
            project_id=validated_args["project_id"]
        )

        return ToolResult(
            success=True,
            data=response_data["data"],
            metadata=response_data["metadata"]
        )
