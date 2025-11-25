"""
Query Mental Notes Tool - DUMB PIPELINE
Receives request → HTTP call to server → Return response
NO LOGIC, NO FORMATTING, NO VALIDATION
"""

from typing import Dict, Any
import httpx

from src.modules.xcp_server.tools.base import BaseTool, ToolDefinition, ToolResult
from src.modules.xcp_server.models.config import ToolContext
from src.modules.core import EventBus, Logger

from .config import QueryMentalNotesConfig


class QueryMentalNotesTool(BaseTool):
    """DUMB PIPELINE - Pass request to server, return response"""

    def __init__(self, event_bus: EventBus, logger: Logger):
        super().__init__(event_bus, logger)
        self.config = QueryMentalNotesConfig()
        self.server_url = "http://localhost:8000"  # TODO: Make configurable

    def get_definition(self) -> ToolDefinition:
        return self.config.get_tool_definition()

    async def execute(self, context: ToolContext, arguments: Dict[str, Any]) -> ToolResult:
        """DUMB PIPELINE: Receive → HTTP GET/POST → Return"""
        try:
            # Add context to arguments
            params = {
                **arguments,
                "user_id": context.user_id,
                "project_id": context.project_id,
                "format": "text"
            }

            # HTTP call to server
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.server_url}/mental-notes/search",
                    json=params,
                    timeout=30.0
                )
                response.raise_for_status()

                # Try to parse as JSON, fallback to text
                try:
                    result = response.json()
                except:
                    result = response.text

            # Return raw response
            return ToolResult(success=True, data=result)

        except Exception as e:
            self.logger.exception(f"HTTP request failed: {str(e)}")
            return ToolResult(success=False, error=str(e))
