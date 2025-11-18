"""
SSE Transport Runner

Runs the MCP server using SSE (Server-Sent Events) transport over HTTP.
"""

from typing import List
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route
import uvicorn

from src.modules.core import EventBus, Logger
from src.modules.xcp_server.models.config import XCPConfig
from src.modules.xcp_server.tools import BaseTool
from src.modules.xcp_server.exceptions import XCPServerNotEnabledError, XCPProtocolError
from src.events.schemas import EventType


class SSERunner:
    """Runs MCP server with SSE transport over HTTP

    This runner exposes the MCP server as an HTTP endpoint, allowing
    multiple clients to connect from different projects/locations.
    """

    def __init__(
        self,
        server: Server,
        config: XCPConfig,
        event_bus: EventBus,
        logger: Logger,
        tools: List[BaseTool],
        host: str = "localhost",
        port: int = 3001
    ):
        """Initialize SSE runner

        Args:
            server: MCP Server instance
            config: XCP server configuration
            event_bus: Event bus for publishing events
            logger: Logger instance
            tools: List of tools (for event metadata)
            host: Host to bind to (default: localhost)
            port: Port to listen on (default: 3001)
        """
        self.server = server
        self.config = config
        self.event_bus = event_bus
        self.logger = logger
        self.tools = tools
        self.host = host
        self.port = port
        self.sse_transport = SseServerTransport("/messages")

    async def handle_sse(self, request):
        """Handle SSE endpoint"""
        async with self.sse_transport.connect_sse(
            request.scope,
            request.receive,
            request._send
        ) as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )

    async def handle_messages(self, request):
        """Handle POST /messages endpoint"""
        async with self.sse_transport.connect_post(
            request.scope,
            request.receive,
            request._send
        ):
            pass  # The transport handles the response

    async def run(self):
        """Run MCP server with SSE transport

        This exposes the server as an HTTP endpoint that can be accessed
        from any project.

        Raises:
            XCPServerNotEnabledError: If server is not enabled in config
            XCPProtocolError: If server encounters a protocol error
        """
        if not self.config.enabled:
            raise XCPServerNotEnabledError()

        self.logger.info(
            "Starting XCP MCP Server with SSE transport",
            extra={
                "server_name": self.config.server_name,
                "version": self.config.server_version,
                "host": self.host,
                "port": self.port,
                "endpoint": f"http://{self.host}:{self.port}/sse"
            }
        )

        # Publish server started event
        self.event_bus.publish(
            EventType.XCP_SERVER_STARTED.value,
            {
                "server_name": self.config.server_name,
                "version": self.config.server_version,
                "transport": "sse",
                "host": self.host,
                "port": self.port,
                "tools": [tool.definition.name for tool in self.tools]
            }
        )

        try:
            # Create Starlette app with SSE transport routes
            app = Starlette(
                routes=[
                    Route("/sse", endpoint=self.handle_sse),
                    Route("/messages", endpoint=self.handle_messages, methods=["POST"]),
                ]
            )

            self.logger.info(
                f"XCP MCP Server listening on http://{self.host}:{self.port}/sse"
            )

            # Run with uvicorn
            config = uvicorn.Config(
                app,
                host=self.host,
                port=self.port,
                log_level=self.config.log_level.value
            )
            server = uvicorn.Server(config)
            await server.serve()

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
