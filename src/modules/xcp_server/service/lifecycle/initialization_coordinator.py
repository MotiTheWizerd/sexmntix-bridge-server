"""Initialization Coordinator - Orchestrates server and tool initialization"""

from dataclasses import dataclass
from typing import Optional
from src.modules.core import EventBus, Logger
from src.modules.embeddings import EmbeddingService
from src.modules.vector_storage.service import VectorStorageService
from src.modules.xcp_server.models.config import XCPConfig
from src.modules.xcp_server.protocol import XCPMCPServer
from src.modules.xcp_server.service.registry import ToolFactory, ToolRegistry


@dataclass
class InitializationResult:
    """Result of server initialization"""
    success: bool
    mcp_server: Optional[XCPMCPServer] = None
    tool_registry: Optional[ToolRegistry] = None
    error: Optional[str] = None


class InitializationCoordinator:
    """Coordinates the initialization sequence of tools and server"""

    def __init__(self):
        """Initialize the coordinator"""
        self._tool_factory = ToolFactory()

    def initialize(
        self,
        config: XCPConfig,
        event_bus: EventBus,
        logger: Logger,
        embedding_service: EmbeddingService,
        vector_storage_service: VectorStorageService,
        db_session_factory
    ) -> InitializationResult:
        """Initialize server and all tools

        Args:
            config: XCP configuration
            event_bus: Event bus for publishing events
            logger: Logger instance
            embedding_service: Embedding generation service
            vector_storage_service: Vector storage and search service
            db_session_factory: Factory for creating database sessions

        Returns:
            InitializationResult with server and registry or error
        """
        try:
            if not config.enabled:
                logger.info("XCP server is disabled")
                return InitializationResult(
                    success=False,
                    error="Server is disabled"
                )

            # Initialize tools
            tools = self._tool_factory.create_tools(
                event_bus=event_bus,
                logger=logger,
                embedding_service=embedding_service,
                db_session_factory=db_session_factory
            )

            # Create tool registry
            tool_registry = ToolRegistry()
            tool_registry.register_many(tools)

            # Create MCP server
            mcp_server = XCPMCPServer(
                config=config,
                event_bus=event_bus,
                logger=logger,
                tools=tools
            )

            # logger.info(
            #     "XCP server initialized successfully",
            #     extra={
            #         "tools_count": len(tools),
            #         "server_name": config.server_name
            #     }
            # )

            return InitializationResult(
                success=True,
                mcp_server=mcp_server,
                tool_registry=tool_registry
            )

        except Exception as e:
            error_msg = f"Failed to initialize XCP server: {str(e)}"
            logger.error(error_msg)
            return InitializationResult(
                success=False,
                error=error_msg
            )
