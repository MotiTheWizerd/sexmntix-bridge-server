"""
XCP Server Service - Main orchestration service for XCP/MCP server

This service coordinates all XCP components using specialized sub-components:
- Tool initialization and registration (via ToolFactory and ToolRegistry)
- MCP server lifecycle management (via ServerLifecycleManager)
- Server initialization coordination (via InitializationCoordinator)
- Server metadata aggregation (via ServerInfoProvider)
- Integration with existing services
"""

from typing import List, Optional
from src.modules.core import EventBus, Logger
from src.modules.embeddings import EmbeddingService
from src.modules.vector_storage.service import VectorStorageService
from src.modules.xcp_server.models.config import XCPConfig, load_xcp_config
from src.modules.xcp_server.tools import BaseTool
from src.modules.xcp_server.protocol import XCPMCPServer
from src.modules.xcp_server.exceptions import XCPServerNotEnabledError
from src.modules.xcp_server.service.registry import ToolRegistry
from src.modules.xcp_server.service.lifecycle import (
    ServerLifecycleManager,
    InitializationCoordinator
)
from src.modules.xcp_server.service.info import ServerInfoProvider


class XCPServerService:
    """Service for managing XCP/MCP server

    This is a facade that orchestrates:
    - Tool instantiation with dependencies (via ToolFactory)
    - Tool registry management (via ToolRegistry)
    - MCP server creation and lifecycle (via InitializationCoordinator and ServerLifecycleManager)
    - Event publishing for XCP operations
    - Integration with embeddings and vector storage
    - Server metadata provision (via ServerInfoProvider)

    Each sub-component has a single, focused responsibility for improved
    testability, maintainability, and extensibility.
    """

    def __init__(
        self,
        event_bus: EventBus,
        logger: Logger,
        embedding_service: EmbeddingService,
        vector_storage_service: VectorStorageService,
        db_session_factory,
        config: Optional[XCPConfig] = None
    ):
        """Initialize XCP server service

        Args:
            event_bus: Event bus for publishing events
            logger: Logger instance
            embedding_service: Embedding generation service
            vector_storage_service: Vector storage and search service
            db_session_factory: Factory for creating database sessions
            config: Optional XCP configuration (loads from env if not provided)
        """
        self.event_bus = event_bus
        self.logger = logger
        self.config = config or load_xcp_config()
        self.embedding_service = embedding_service
        self.vector_storage_service = vector_storage_service
        self.db_session_factory = db_session_factory

        # Components
        self._initialization_coordinator = InitializationCoordinator()
        self._lifecycle_manager: Optional[ServerLifecycleManager] = None
        self._tool_registry: Optional[ToolRegistry] = None
        self._info_provider = ServerInfoProvider()

        # MCP server instance (for backward compatibility)
        self.mcp_server: Optional[XCPMCPServer] = None

        # Tools (for backward compatibility)
        self.tools: List[BaseTool] = []

        # self.logger.info(
        #     "XCPServerService initialized",
        #     extra={
        #         "enabled": self.config.enabled,
        #         "server_name": self.config.server_name,
        #         "transport": self.config.transport.value
        #     }
        # )

    def initialize(self):
        """Initialize the XCP server and tools

        This method should be called during application startup.
        Delegates initialization to InitializationCoordinator.
        """
        # Delegate to initialization coordinator
        result = self._initialization_coordinator.initialize(
            config=self.config,
            event_bus=self.event_bus,
            logger=self.logger,
            embedding_service=self.embedding_service,
            vector_storage_service=self.vector_storage_service,
            db_session_factory=self.db_session_factory
        )

        if not result.success:
            self.logger.warning(f"XCP initialization result: {result.error}")
            return

        # Store results for use
        self.mcp_server = result.mcp_server
        self._tool_registry = result.tool_registry
        self.tools = result.tool_registry.get_all()

        # Create lifecycle manager
        self._lifecycle_manager = ServerLifecycleManager(
            server=self.mcp_server,
            config=self.config,
            logger=self.logger
        )

    async def start(self):
        """Start the MCP server

        This method runs the MCP server with the configured transport.
        For stdio transport, this is a blocking call.

        Delegates to ServerLifecycleManager.
        """
        if not self.config.enabled:
            raise XCPServerNotEnabledError()

        if not self._lifecycle_manager:
            raise RuntimeError("XCP server not initialized. Call initialize() first.")

        await self._lifecycle_manager.start()

    async def start_background(self):
        """Start the MCP server as a background task

        Returns:
            asyncio.Task: The background task

        Delegates to ServerLifecycleManager.
        """
        if not self.config.enabled:
            self.logger.info("XCP server is disabled, not starting background task")
            return None

        if not self._lifecycle_manager:
            raise RuntimeError("XCP server not initialized. Call initialize() first.")

        return await self._lifecycle_manager.start_background()

    async def stop(self):
        """Stop the MCP server gracefully

        Delegates to ServerLifecycleManager.
        """
        if not self._lifecycle_manager:
            return

        await self._lifecycle_manager.stop()

    def is_enabled(self) -> bool:
        """Check if XCP server is enabled

        Returns:
            bool: True if enabled
        """
        return self.config.enabled

    def get_tool_names(self) -> List[str]:
        """Get list of registered tool names

        Returns:
            List of tool names

        Delegates to ToolRegistry via ServerInfoProvider.
        """
        if not self._tool_registry:
            return []
        return self._info_provider.get_tool_names(self._tool_registry)

    def get_server_info(self) -> dict:
        """Get server information

        Returns:
            Dictionary with server information

        Delegates to ServerInfoProvider.
        """
        if not self._tool_registry:
            return {
                "enabled": self.config.enabled,
                "server_name": self.config.server_name,
                "server_version": self.config.server_version,
                "transport": self.config.transport.value,
                "tools": [],
                "tools_count": 0
            }
        return self._info_provider.get_server_info(self.config, self._tool_registry)
