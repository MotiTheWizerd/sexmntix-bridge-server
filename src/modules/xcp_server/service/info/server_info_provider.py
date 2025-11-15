"""Server Info Provider - Aggregates and provides server metadata"""

from typing import List
from src.modules.xcp_server.models.config import XCPConfig
from src.modules.xcp_server.service.registry import ToolRegistry


class ServerInfoProvider:
    """Provides aggregated server and tool information"""

    @staticmethod
    def get_server_info(
        config: XCPConfig,
        tool_registry: ToolRegistry
    ) -> dict:
        """Get comprehensive server information

        Args:
            config: XCP configuration
            tool_registry: Tool registry with registered tools

        Returns:
            Dictionary with server information
        """
        return {
            "enabled": config.enabled,
            "server_name": config.server_name,
            "server_version": config.server_version,
            "transport": config.transport.value,
            "tools": tool_registry.get_tool_names(),
            "tools_count": tool_registry.count(),
            "default_user_id": config.default_user_id,
            "default_project_id": config.default_project_id
        }

    @staticmethod
    def get_tool_names(tool_registry: ToolRegistry) -> List[str]:
        """Get list of all tool names

        Args:
            tool_registry: Tool registry with registered tools

        Returns:
            List of tool names
        """
        return tool_registry.get_tool_names()

    @staticmethod
    def get_tool_count(tool_registry: ToolRegistry) -> int:
        """Get count of registered tools

        Args:
            tool_registry: Tool registry with registered tools

        Returns:
            Number of registered tools
        """
        return tool_registry.count()
