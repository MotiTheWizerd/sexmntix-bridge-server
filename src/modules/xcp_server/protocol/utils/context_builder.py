"""
Context Builder

Builds ToolContext instances for tool execution from server configuration
and request parameters.
"""

from typing import Optional
from src.modules.xcp_server.models.config import XCPConfig, ToolContext


class ContextBuilder:
    """Builds ToolContext instances for tool execution

    This class creates properly configured ToolContext objects that provide
    tools with the necessary execution context (user_id, project_id, session_id).
    """

    def __init__(self, config: XCPConfig):
        """Initialize context builder

        Args:
            config: XCP server configuration with default values
        """
        self.config = config

    def build_context(
        self,
        user_id: Optional[int] = None,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> ToolContext:
        """Build a ToolContext with defaults from config

        Args:
            user_id: Optional user ID (defaults to config.default_user_id)
            project_id: Optional project ID (defaults to config.default_project_id)
            session_id: Optional session ID (defaults to None)

        Returns:
            ToolContext instance ready for tool execution
        """
        return ToolContext(
            user_id=user_id or self.config.default_user_id,
            project_id=project_id or self.config.default_project_id,
            session_id=session_id
        )

    def build_default_context(self) -> ToolContext:
        """Build a ToolContext with all default values from config

        Returns:
            ToolContext instance with config defaults
        """
        return self.build_context()
