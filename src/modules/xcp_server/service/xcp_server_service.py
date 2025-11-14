"""
XCP Server Service - Main orchestration service for XCP/MCP server

This service coordinates all XCP components:
- Tool initialization and registration
- MCP server lifecycle management
- Integration with existing services
"""

from typing import List, Optional
import asyncio
from contextlib import asynccontextmanager

from src.services.base_service import BaseService
from src.modules.core import EventBus, Logger
from src.modules.embeddings import EmbeddingService
from src.modules.vector_storage.service import VectorStorageService
from src.modules.xcp_server.models.config import XCPConfig, load_xcp_config
from src.modules.xcp_server.tools import (
    BaseTool,
    SemanticSearchTool,
    StoreMemoryTool,
    EmbeddingTool,
    StoreMentalNoteTool,
    QueryMentalNotesTool
)
from src.modules.xcp_server.protocol import XCPMCPServer
from src.modules.xcp_server.exceptions import XCPServerNotEnabledError


class XCPServerService(BaseService):
    """Service for managing XCP/MCP server

    Orchestrates:
    - Tool instantiation with dependencies
    - MCP server creation and lifecycle
    - Event publishing for XCP operations
    - Integration with embeddings and vector storage
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
        super().__init__(event_bus, logger)

        self.config = config or load_xcp_config()
        self.embedding_service = embedding_service
        self.vector_storage_service = vector_storage_service
        self.db_session_factory = db_session_factory

        # MCP server instance
        self.mcp_server: Optional[XCPMCPServer] = None

        # Tools
        self.tools: List[BaseTool] = []

        # Server task
        self._server_task: Optional[asyncio.Task] = None

        self.logger.info(
            "XCPServerService initialized",
            extra={
                "enabled": self.config.enabled,
                "server_name": self.config.server_name,
                "transport": self.config.transport.value
            }
        )

    def _register_handlers(self):
        """Register event handlers"""
        # Could subscribe to application events if needed
        pass

    def _initialize_tools(self) -> List[BaseTool]:
        """Initialize all MCP tools with their dependencies

        Returns:
            List of initialized tools
        """
        tools = []

        # 1. Semantic Search Tool
        semantic_search_tool = SemanticSearchTool(
            event_bus=self.event_bus,
            logger=self.logger,
            vector_storage_service=self.vector_storage_service
        )
        tools.append(semantic_search_tool)

        # 2. Store Memory Tool
        store_memory_tool = StoreMemoryTool(
            event_bus=self.event_bus,
            logger=self.logger,
            db_session_factory=self.db_session_factory
        )
        tools.append(store_memory_tool)

        # 3. Embedding Tool
        embedding_tool = EmbeddingTool(
            event_bus=self.event_bus,
            logger=self.logger,
            embedding_service=self.embedding_service
        )
        tools.append(embedding_tool)

        # 4. Store Mental Note Tool
        store_mental_note_tool = StoreMentalNoteTool(
            event_bus=self.event_bus,
            logger=self.logger,
            db_session_factory=self.db_session_factory
        )
        tools.append(store_mental_note_tool)

        # 5. Query Mental Notes Tool
        query_mental_notes_tool = QueryMentalNotesTool(
            event_bus=self.event_bus,
            logger=self.logger,
            db_session_factory=self.db_session_factory
        )
        tools.append(query_mental_notes_tool)

        self.logger.info(f"Initialized {len(tools)} MCP tools")

        return tools

    def initialize(self):
        """Initialize the XCP server and tools

        This method should be called during application startup.
        """
        if not self.config.enabled:
            self.logger.info("XCP server is disabled")
            return

        # Initialize tools
        self.tools = self._initialize_tools()

        # Create MCP server
        self.mcp_server = XCPMCPServer(
            config=self.config,
            event_bus=self.event_bus,
            logger=self.logger,
            tools=self.tools
        )

        self.logger.info(
            "XCP server initialized successfully",
            extra={
                "tools_count": len(self.tools),
                "server_name": self.config.server_name
            }
        )

    async def start(self):
        """Start the MCP server

        This method runs the MCP server with the configured transport.
        For stdio transport, this is a blocking call.
        """
        if not self.config.enabled:
            raise XCPServerNotEnabledError()

        if not self.mcp_server:
            raise RuntimeError("XCP server not initialized. Call initialize() first.")

        self.logger.info("Starting XCP server")

        if self.config.transport.value == "stdio":
            # Run stdio server (blocking)
            await self.mcp_server.run_stdio()
        else:
            raise NotImplementedError(
                f"Transport '{self.config.transport}' not yet implemented"
            )

    async def start_background(self):
        """Start the MCP server as a background task

        Returns:
            asyncio.Task: The background task
        """
        if not self.config.enabled:
            self.logger.info("XCP server is disabled, not starting background task")
            return

        if not self.mcp_server:
            raise RuntimeError("XCP server not initialized. Call initialize() first.")

        self.logger.info("Starting XCP server in background")

        self._server_task = asyncio.create_task(self.start())
        return self._server_task

    async def stop(self):
        """Stop the MCP server gracefully"""
        if self._server_task:
            self.logger.info("Stopping XCP server")

            # Cancel the server task
            self._server_task.cancel()

            try:
                await self._server_task
            except asyncio.CancelledError:
                self.logger.info("XCP server task cancelled")

            self._server_task = None

        if self.mcp_server:
            await self.mcp_server.shutdown()

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
        """
        return [tool.definition.name for tool in self.tools]

    def get_server_info(self) -> dict:
        """Get server information

        Returns:
            Dictionary with server information
        """
        return {
            "enabled": self.config.enabled,
            "server_name": self.config.server_name,
            "server_version": self.config.server_version,
            "transport": self.config.transport.value,
            "tools": self.get_tool_names(),
            "default_user_id": self.config.default_user_id,
            "default_project_id": self.config.default_project_id
        }
