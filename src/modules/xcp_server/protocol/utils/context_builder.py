"""
Context Builder

Builds ToolContext instances for tool execution from server configuration
and request parameters.
"""

from typing import Optional
from src.modules.xcp_server.models.config import XCPConfig, ToolContext
from src.modules.core import Logger


class ContextBuilder:
    """Builds ToolContext instances for tool execution

    This class creates properly configured ToolContext objects that provide
    tools with the necessary execution context (user_id, project_id, session_id).
    """

    def __init__(self, config: XCPConfig, logger: Optional[Logger] = None):
        """Initialize context builder

        Args:
            config: XCP server configuration with default values
            logger: Optional logger instance for debug logging
        """
        self.config = config
        self.logger = logger

    def build_context(
        self,
        session_id: Optional[str] = None
    ) -> ToolContext:
        """Build a ToolContext

        Args:
            session_id: Optional session ID (defaults to None)

        Returns:
            ToolContext instance ready for tool execution
        """
        return ToolContext(
            session_id=session_id,
            user_id=self.config.user_id,
            project_id=self.config.project_id
        )

    def build_default_context(self) -> ToolContext:
        """Build a ToolContext with all default values from config

        Returns:
            ToolContext instance with config defaults
        """
        return self.build_context()
