"""
Store Memory Tool - Dumb Pipeline Implementation

ARCHITECTURAL PRINCIPLE: This tool is a DUMB PIPELINE.
It forwards requests to the backend API at http://localhost:8000 with NO business logic.
All validation, building, and formatting happens in the backend.
"""
import os
from typing import Dict, Any
import httpx

from src.modules.xcp_server.tools.base import BaseTool, ToolDefinition, ToolResult
from src.modules.xcp_server.models.config import ToolContext
from src.modules.core import EventBus, Logger

from src.modules.xcp_server.tools.store_memory.config import StoreMemoryConfig


class StoreMemoryTool(BaseTool):
    """
    Store memory tool - Simple HTTP proxy

    This tool forwards memory storage requests to the backend API.
    NO business logic, validation, or formatting in this layer.
    """

    def __init__(self, event_bus: EventBus, logger: Logger):
        """
        Initialize store memory tool

        Args:
            event_bus: Event bus (required by BaseTool but not used in dumb pipeline)
            logger: Logger instance
        """
        super().__init__(event_bus, logger)
        self.api_base_url = "http://localhost:8000"

    def get_definition(self) -> ToolDefinition:
        """Get tool definition for MCP registration"""
        return StoreMemoryConfig.get_tool_definition()

    async def execute(
        self,
        context: ToolContext,
        arguments: Dict[str, Any]
    ) -> ToolResult:
        """
        Execute memory storage by forwarding to backend API

        This is a DUMB PIPELINE - just forwards the request to the backend.
        No validation, no formatting, no business logic here.

        Args:
            context: Execution context (user_id, project_id defaults)
            arguments: Memory log parameters

        Returns:
            ToolResult: Response from backend API
        """
        try:
            # Unwrap MCP "memory_log" parameter wrapper
            # MCP SDK wraps all arguments with the parameter name from config
            request_payload = arguments.get("memory_log", arguments)

            # Inject required IDs from context/environment to avoid random/placeholder values
            # Prefer explicit env vars (XCP_USER_ID/XCP_PROJECT_ID) and fall back to context
            env_user_id = os.getenv("XCP_USER_ID") or context.user_id
            env_project_id = os.getenv("XCP_PROJECT_ID") or context.project_id

            enriched_payload = {
                **request_payload,
                "user_id": env_user_id,
                "project_id": env_project_id,
                
            }

            # Only add session_id if provided in context and not already present
            if context.session_id and "session_id" not in enriched_payload:
                enriched_payload["session_id"] = context.session_id

            self.logger.info(f"[STORE_MEMORY] Forwarding request to backend API")

            # Forward request to backend API
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.api_base_url}/memory-logs",
                    json=enriched_payload
                )
                response.raise_for_status()

                # Try to parse as JSON, fallback to text
                try:
                    result = response.json()
                except:
                    result = response.text

            self.logger.info(f"[STORE_MEMORY] Memory stored successfully")

            # Return a concise confirmation while keeping the raw response in metadata
            if isinstance(result, dict):
                memory_id = result.get("id") or result.get("memory_log_id")
                message = f"memory log created{f' (id: {memory_id})' if memory_id else ''}"
            else:
                message = "memory log created"

            return ToolResult(
                success=True,
                data=message,
                metadata={"response": result}
            )

        except httpx.HTTPError as e:
            self.logger.error(f"[STORE_MEMORY] HTTP error: {e}")
            return ToolResult(
                success=False,
                data={},
                message=f"Storage failed: {str(e)}"
            )

        except Exception as e:
            self.logger.error(f"[STORE_MEMORY] Unexpected error: {e}")
            return ToolResult(
                success=False,
                data={},
                message=f"Storage failed: {str(e)}"
            )
