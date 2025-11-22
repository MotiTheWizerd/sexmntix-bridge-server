"""
Search Memory By Date Tool - Simple HTTP Proxy Implementation

ARCHITECTURAL PRINCIPLE: This tool is a DUMB PIPELINE.
It forwards requests to the backend API at http://localhost:8000 with NO business logic.
All validation, date calculation, filtering, and formatting happens in the backend.
"""

from typing import Dict, Any
import httpx

from src.modules.xcp_server.tools.base import BaseTool, ToolDefinition, ToolResult
from src.modules.xcp_server.models.config import ToolContext
from src.modules.core import EventBus, Logger

from src.modules.xcp_server.tools.search_memory_by_date.config import SEARCH_MEMORY_BY_DATE_TOOL_DEF


class SearchMemoryByDateTool(BaseTool):
    """
    Search memory by date tool - Simple HTTP proxy

    This tool forwards date-filtered search requests to the backend API.
    NO business logic, validation, or formatting in this layer.
    """

    def __init__(self, event_bus: EventBus, logger: Logger):
        """
        Initialize search memory by date tool

        Args:
            event_bus: Event bus (required by BaseTool but not used in dumb pipeline)
            logger: Logger instance
        """
        super().__init__(event_bus, logger)
        self.api_base_url = "http://localhost:8000"

    def get_definition(self) -> ToolDefinition:
        """Get tool definition for MCP registration"""
        return SEARCH_MEMORY_BY_DATE_TOOL_DEF

    async def execute(
        self,
        context: ToolContext,
        arguments: Dict[str, Any]
    ) -> ToolResult:
        """
        Execute date-filtered search by forwarding to backend API

        This is a DUMB PIPELINE - just forwards the request to the backend.
        No validation, no formatting, no business logic here.

        Args:
            context: Execution context (user_id, project_id defaults)
            arguments: Search parameters (query, limit, start_date, end_date, time_period)

        Returns:
            ToolResult: Response from backend API
        """
        try:
            # Get user_id and project_id from context (set from environment variables)
            user_id = context.user_id
            project_id = context.project_id

            # Build request payload - just pass through the arguments
            request_payload = {
                "user_id": user_id,
                "project_id": project_id,
                "query": arguments.get("query", ""),
                "limit": arguments.get("limit", 10),
            }

            # Add optional date parameters if provided
            if "start_date" in arguments:
                request_payload["start_date"] = arguments["start_date"]
            if "end_date" in arguments:
                request_payload["end_date"] = arguments["end_date"]
            if "time_period" in arguments:
                request_payload["time_period"] = arguments["time_period"]

            self.logger.info(
                f"[SEARCH_BY_DATE] Forwarding search request to backend API: {request_payload.get('query', '')[:50]}..."
            )

            # Forward request to backend API
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.api_base_url}/memory-logs/search-by-date",
                    json=request_payload
                )
                response.raise_for_status()

            # Return response as-is (backend handles all formatting)
            result_text = response.text

            self.logger.info(
                f"[SEARCH_BY_DATE] Search completed successfully, "
                f"returned {len(result_text)} characters"
            )

            return ToolResult(
                success=True,
                data={"result": result_text},
                message="Search completed successfully"
            )

        except httpx.HTTPError as e:
            self.logger.error(f"[SEARCH_BY_DATE] HTTP error: {e}")
            return ToolResult(
                success=False,
                data={},
                message=f"Search failed: {str(e)}"
            )

        except Exception as e:
            self.logger.error(f"[SEARCH_BY_DATE] Unexpected error: {e}")
            return ToolResult(
                success=False,
                data={},
                message=f"Search failed: {str(e)}"
            )
