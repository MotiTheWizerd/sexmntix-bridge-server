"""Server Lifecycle Manager - Handles MCP server start/stop operations"""

import asyncio
from typing import Optional
from src.modules.core import Logger
from src.modules.xcp_server.models.config import XCPConfig
from src.modules.xcp_server.protocol import XCPMCPServer
from src.modules.xcp_server.exceptions import XCPServerNotEnabledError


class ServerLifecycleManager:
    """Manages the lifecycle of the MCP server (start, stop, task management)"""

    def __init__(
        self,
        server: XCPMCPServer,
        config: XCPConfig,
        logger: Logger
    ):
        """Initialize server lifecycle manager

        Args:
            server: The XCPMCPServer instance
            config: XCP configuration
            logger: Logger instance
        """
        self._server = server
        self._config = config
        self._logger = logger
        self._server_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start the MCP server (blocking)

        This method runs the MCP server with the configured transport.
        For stdio transport, this is a blocking call.

        Raises:
            XCPServerNotEnabledError: If server is not enabled
            RuntimeError: If server is not properly initialized
        """
        if not self._config.enabled:
            raise XCPServerNotEnabledError()

        self._logger.info("Starting XCP server")

        if self._config.transport.value == "stdio":
            # Run stdio server (blocking)
            await self._server.run_stdio()
        elif self._config.transport.value == "sse":
            # Run SSE server (blocking)
            await self._server.run_sse()
        else:
            raise NotImplementedError(
                f"Transport '{self._config.transport}' not yet implemented"
            )

    async def start_background(self) -> Optional[asyncio.Task]:
        """Start the MCP server as a background task

        Returns:
            asyncio.Task: The background task, or None if server is disabled
        """
        if not self._config.enabled:
            self._logger.info("XCP server is disabled, not starting background task")
            return None

        self._logger.info("Starting XCP server in background")

        self._server_task = asyncio.create_task(self.start())
        return self._server_task

    async def stop(self) -> None:
        """Stop the MCP server gracefully

        Cancels the background task if running and shuts down the server.
        """
        if self._server_task:
            self._logger.info("Stopping XCP server")

            # Cancel the server task
            self._server_task.cancel()

            try:
                await self._server_task
            except asyncio.CancelledError:
                self._logger.info("XCP server task cancelled")

            self._server_task = None

        await self._server.shutdown()

    def is_running(self) -> bool:
        """Check if server is currently running

        Returns:
            bool: True if server task is running, False otherwise
        """
        return self._server_task is not None and not self._server_task.done()

    def get_task(self) -> Optional[asyncio.Task]:
        """Get the current server task if running

        Returns:
            The asyncio.Task or None if not running
        """
        return self._server_task
