"""
MCP Server Implementation

Implements the Model Context Protocol (MCP) server that exposes semantic memory
capabilities to AI assistants through standardized tools.
"""

import asyncio
from typing import Dict, List, Any, Optional
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from src.modules.core import EventBus, Logger
from src.modules.xcp_server.models.config import XCPConfig, ToolContext
from src.modules.xcp_server.tools import BaseTool
from src.modules.xcp_server.exceptions import (
    XCPProtocolError,
    XCPToolExecutionError,
    XCPServerNotEnabledError
)
from src.events.schemas import EventType


class XCPMCPServer:
    """MCP Server for Semantic Bridge

    This server exposes semantic memory capabilities through MCP tools,
    allowing AI assistants to:
    - Search memories using vector similarity
    - Store new memories with automatic embedding
    - Generate text embeddings
    - Store and query mental notes
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

        # Session tracking
        self.active_sessions: Dict[str, Any] = {}

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
        """Setup MCP protocol handlers"""

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List all available tools"""
            self.logger.debug("MCP client requested tool list")

            tools = []
            for tool in self.tools:
                definition = tool.definition
                mcp_schema = definition.to_mcp_schema()

                # Convert to MCP Tool type
                tools.append(
                    Tool(
                        name=mcp_schema["name"],
                        description=mcp_schema["description"],
                        inputSchema=mcp_schema["inputSchema"]
                    )
                )

            self.logger.info(f"Returned {len(tools)} tools to MCP client")
            return tools

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Execute a tool

            Args:
                name: Tool name
                arguments: Tool arguments

            Returns:
                List of TextContent with tool results
            """
            self.logger.info(
                f"MCP tool call received",
                extra={"tool_name": name, "arguments": arguments}
            )

            # Get tool from registry
            tool = self.tool_registry.get(name)
            if not tool:
                error_msg = f"Tool '{name}' not found"
                self.logger.error(error_msg)
                return [TextContent(
                    type="text",
                    text=f"Error: {error_msg}"
                )]

            try:
                # Create execution context
                context = ToolContext(
                    user_id=self.config.default_user_id,
                    project_id=self.config.default_project_id,
                    session_id=None  # Could be enhanced to track MCP session
                )

                # Execute tool
                result = await tool.run(context, arguments)

                # Format response
                if result.success:
                    import json
                    response_text = json.dumps(result.data, indent=2, default=str)
                    return [TextContent(type="text", text=response_text)]
                else:
                    error_text = f"Tool execution failed: {result.error}"
                    if result.error_code:
                        error_text = f"[{result.error_code}] {error_text}"
                    return [TextContent(type="text", text=error_text)]

            except XCPToolExecutionError as e:
                error_msg = f"Tool execution error: {e.message}"
                self.logger.error(error_msg, extra={"error_code": e.code})
                return [TextContent(type="text", text=error_msg)]

            except Exception as e:
                error_msg = f"Unexpected error executing tool '{name}': {str(e)}"
                self.logger.exception(error_msg)
                return [TextContent(type="text", text=error_msg)]

    async def run_stdio(self):
        """Run MCP server with stdio transport

        This is the standard way to run MCP servers for local AI assistants
        like Claude Desktop.
        """
        if not self.config.enabled:
            raise XCPServerNotEnabledError()

        self.logger.info(
            "Starting XCP MCP Server with stdio transport",
            extra={
                "server_name": self.config.server_name,
                "version": self.config.server_version
            }
        )

        # Publish server started event
        self.event_bus.publish(
            EventType.XCP_SERVER_STARTED.value,
            {
                "server_name": self.config.server_name,
                "version": self.config.server_version,
                "transport": "stdio",
                "tools": [tool.definition.name for tool in self.tools]
            }
        )

        try:
            # Run stdio server (blocks until client disconnects)
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    self.server.create_initialization_options()
                )

        except Exception as e:
            self.logger.exception(f"MCP server error: {str(e)}")
            raise XCPProtocolError(f"Server failed: {str(e)}")

        finally:
            self.logger.info("XCP MCP Server stopped")

            # Publish server stopped event
            self.event_bus.publish(
                EventType.XCP_SERVER_STOPPED.value,
                {"server_name": self.config.server_name}
            )

    async def shutdown(self):
        """Gracefully shutdown the MCP server"""
        self.logger.info("Shutting down XCP MCP Server")

        # Cleanup any active sessions
        self.active_sessions.clear()

        # Publish shutdown event
        self.event_bus.publish(
            EventType.XCP_SERVER_STOPPED.value,
            {"server_name": self.config.server_name}
        )
