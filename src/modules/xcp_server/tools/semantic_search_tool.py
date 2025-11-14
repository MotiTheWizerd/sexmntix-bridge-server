"""
Semantic Search Tool - MCP Tool for searching memories using vector similarity

Enables AI assistants to search through stored memories using semantic similarity.
"""

from typing import Dict, Any, Optional
from src.modules.xcp_server.tools.base import BaseTool, ToolDefinition, ToolParameter, ToolResult
from src.modules.xcp_server.models.config import ToolContext
from src.modules.xcp_server.exceptions import XCPToolExecutionError
from src.modules.core import EventBus, Logger
from src.modules.embeddings import EmbeddingService
from src.api.dependencies.vector_storage import create_vector_storage_service


class SemanticSearchTool(BaseTool):
    """Tool for semantic search in memory logs using vector similarity

    This tool allows AI assistants to search through stored memories
    using natural language queries. It leverages vector embeddings
    to find semantically similar memories.
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

    def get_definition(self) -> ToolDefinition:
        """Get tool definition for MCP registration

        Returns:
            ToolDefinition: Tool metadata and parameter schema
        """
        return ToolDefinition(
            name="semantic_search",
            description=(
                "Search through stored memories using semantic similarity. "
                "Provide a natural language query and get back the most relevant memories. "
                "Useful for finding related information, past solutions, or similar contexts."
            ),
            parameters=[
                ToolParameter(
                    name="query",
                    type="string",
                    description="The search query in natural language (e.g., 'authentication bug fixes', 'database optimization tips')",
                    required=True
                ),
                ToolParameter(
                    name="limit",
                    type="number",
                    description="Maximum number of results to return (default: 10, max: 50)",
                    required=False,
                    default=10
                ),
                ToolParameter(
                    name="min_similarity",
                    type="number",
                    description="Minimum similarity score threshold from 0.0 to 1.0 (default: 0.0). Higher values return more relevant results.",
                    required=False,
                    default=0.0
                ),
                ToolParameter(
                    name="user_id",
                    type="number",
                    description="Override the default user ID for this search (optional)",
                    required=False
                ),
                ToolParameter(
                    name="project_id",
                    type="string",
                    description="Override the default project ID for this search (optional)",
                    required=False
                )
            ]
        )

    async def execute(
        self,
        context: ToolContext,
        arguments: Dict[str, Any]
    ) -> ToolResult:
        """Execute semantic search

        Args:
            context: Execution context with user/project defaults
            arguments: Validated arguments containing query, limit, etc.

        Returns:
            ToolResult: Search results with similarity scores
        """
        try:
            # Extract arguments with context overrides
            query = arguments["query"]
            limit = min(int(arguments.get("limit", 10)), 50)  # Cap at 50
            min_similarity = float(arguments.get("min_similarity", 0.0))
            user_id = str(arguments.get("user_id", context.user_id))
            project_id = arguments.get("project_id", context.project_id)

            # Validate min_similarity range
            if not 0.0 <= min_similarity <= 1.0:
                return ToolResult(
                    success=False,
                    error="min_similarity must be between 0.0 and 1.0",
                    error_code="INVALID_SIMILARITY_RANGE"
                )

            self.logger.info(
                f"Executing semantic search",
                extra={
                    "query": query,
                    "user_id": user_id,
                    "project_id": project_id,
                    "limit": limit,
                    "min_similarity": min_similarity
                }
            )

            # Create per-user/project vector storage service
            vector_service = create_vector_storage_service(
                user_id=user_id,
                project_id=project_id,
                embedding_service=self.embedding_service,
                event_bus=self.event_bus,
                logger=self.logger
            )

            # Perform semantic search
            results = await vector_service.search_similar_memories(
                query=query,
                user_id=user_id,
                project_id=project_id,
                limit=limit,
                min_similarity=min_similarity
            )

            # Format results for better readability
            formatted_results = []
            for result in results:
                # Get content from document, not metadata
                document = result.get("document", {})
                formatted_results.append({
                    "memory_id": result.get("id"),
                    "content": document.get("content", ""),
                    "similarity_score": round(result.get("distance", 0.0), 4),
                    "metadata": result.get("metadata", {}),
                    "document": document,  # Include full document for reference
                    "created_at": result.get("metadata", {}).get("created_at")
                })

            return ToolResult(
                success=True,
                data={
                    "query": query,
                    "result_count": len(formatted_results),
                    "results": formatted_results,
                    "filters_applied": {
                        "min_similarity": min_similarity,
                        "limit": limit
                    }
                },
                metadata={
                    "user_id": user_id,
                    "project_id": project_id
                }
            )

        except Exception as e:
            self.logger.exception(f"Semantic search failed: {str(e)}")
            raise XCPToolExecutionError(
                tool_name="semantic_search",
                message=f"Search operation failed: {str(e)}",
                original_error=e
            )
