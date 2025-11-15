"""
STDIO Transport Runner

Runs the MCP server using stdio transport for local AI assistant integration.
"""

from typing import List
from mcp.server import Server
from mcp.server.stdio import stdio_server

from src.modules.core import EventBus, Logger
from src.modules.xcp_server.models.config import XCPConfig
from src.modules.xcp_server.tools import BaseTool
from src.modules.xcp_server.exceptions import XCPServerNotEnabledError, XCPProtocolError
from src.events.schemas import EventType


class StdioRunner:
    """Runs MCP server with stdio transport

    This runner handles the stdio transport lifecycle including startup,
    event publishing, and graceful shutdown.
    """

    def __init__(
        self,
        server: Server,
        config: XCPConfig,
        event_bus: EventBus,
        logger: Logger,
        tools: List[BaseTool]
    ):
        """Initialize stdio runner

        Args:
            server: MCP Server instance
            config: XCP server configuration
            event_bus: Event bus for publishing events
            logger: Logger instance
            tools: List of tools (for event metadata)
        """
        self.server = server
        self.config = config
        self.event_bus = event_bus
        self.logger = logger
        self.tools = tools

    async def run(self):
        """Run MCP server with stdio transport

        This is the standard way to run MCP servers for local AI assistants
        like Claude Desktop.

        Raises:
            XCPServerNotEnabledError: If server is not enabled in config
            XCPProtocolError: If server encounters a protocol error
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
