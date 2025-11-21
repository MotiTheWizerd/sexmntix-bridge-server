"""
MCP Server Implementation

Implements the Model Context Protocol (MCP) server that exposes semantic memory
capabilities to AI assistants through standardized tools.

This module has been refactored to use smaller, focused components:
- handlers/: MCP protocol request handlers
- session/: Session management
- transport/: Transport layer (stdio, etc)
- utils/: Helper utilities for formatting and context building
"""

from typing import Dict, List
from mcp.server import Server

from src.modules.core import EventBus, Logger
from src.modules.xcp_server.models.config import XCPConfig
from src.modules.xcp_server.tools import BaseTool
from src.modules.xcp_server.protocol.handlers import ToolListHandler, ToolCallHandler
from src.modules.xcp_server.protocol.session import SessionManager
from src.modules.xcp_server.protocol.transport import StdioRunner, SSERunner
from src.modules.xcp_server.protocol.utils import ContextBuilder
from src.events.schemas import EventType


class XCPMCPServer:
    """MCP Server for Semantic Bridge

    This server exposes semantic memory capabilities through MCP tools,
    allowing AI assistants to:
    - Search memories using vector similarity
    - Store new memories with automatic embedding
    - Generate text embeddings
    - Store and query mental notes

    The server is composed of focused components:
    - ToolListHandler: Handles tool discovery
    - ToolCallHandler: Handles tool execution
    - SessionManager: Tracks active sessions
    - StdioRunner: Manages stdio transport
    - ContextBuilder: Creates execution contexts
    """

    def __init__(
        self,
        config: XCPConfig,
        event_bus: EventBus,
        logger: Logger,
        tools: List[BaseTool]
    ):
        """Initialize MCP server

        Args:
            config: XCP server configuration
            event_bus: Event bus for publishing events
            logger: Logger instance
            tools: List of MCP tools to expose
        """
        self.config = config
        self.event_bus = event_bus
        self.logger = logger
        self.tools = tools

        # Create MCP server instance
        self.server = Server(name=config.server_name)

        # Tool registry
        self.tool_registry: Dict[str, BaseTool] = {}

        # Initialize components
        self.session_manager = SessionManager(logger)
        self.context_builder = ContextBuilder(config, logger)
        self.tool_list_handler = ToolListHandler(tools, logger)
        self.tool_call_handler = ToolCallHandler(
            self.tool_registry,
            self.context_builder,
            logger
        )
        self.stdio_runner = StdioRunner(
            self.server,
            config,
            event_bus,
            logger,
            tools
        )
        self.sse_runner = SSERunner(
            self.server,
            config,
            event_bus,
            logger,
            tools,
            host=config.sse_host,
            port=config.sse_port
        )

        # Register all tools
        self._register_tools()

        # Setup MCP handlers
        self._setup_handlers()

        self.logger.info(
            f"XCP MCP Server initialized",
            extra={
                "server_name": config.server_name,
                "server_version": config.server_version,
                "tools_count": len(self.tools)
            }
        )

    def _register_tools(self):
        """Register all tools with the MCP server"""
        for tool in self.tools:
            definition = tool.definition
            self.tool_registry[definition.name] = tool

            self.logger.info(
                f"Registered tool: {definition.name}",
                extra={"tool_name": definition.name}
            )

    def _setup_handlers(self):
        """Setup MCP protocol handlers

        Delegates to handler components for actual implementation.
        """

        @self.server.list_tools()
        async def list_tools():
            """List all available tools - delegates to ToolListHandler"""
            return await self.tool_list_handler.handle_list_tools()

        # Note: This handler is marked as "probably dead code" in the original
        # implementation. Preserving for backward compatibility but documenting
        # the concern for future investigation.
        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict):
            """Execute a tool - delegates to ToolCallHandler"""
            return await self.tool_call_handler.handle_call_tool(name, arguments)

    async def run_stdio(self):
        """Run MCP server with stdio transport

        Delegates to StdioRunner for transport management.

        This is the standard way to run MCP servers for local AI assistants
        like Claude Desktop.
        """
        await self.stdio_runner.run()

    async def run_sse(self):
        """Run MCP server with SSE transport over HTTP

        Delegates to SSERunner for transport management.

        This exposes the MCP server as an HTTP endpoint, allowing
        multiple clients to connect from different projects/locations.
        """
        await self.sse_runner.run()

    async def shutdown(self):
        """Gracefully shutdown the MCP server"""
        self.logger.info("Shutting down XCP MCP Server")

        # Cleanup any active sessions using SessionManager
        self.session_manager.clear_all_sessions()

        # Publish shutdown event
        self.event_bus.publish(
            EventType.XCP_SERVER_STOPPED.value,
            {"server_name": self.config.server_name}
        )
