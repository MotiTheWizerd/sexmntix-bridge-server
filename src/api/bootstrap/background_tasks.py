"""
Background task management for FastAPI application.

Handles lifecycle of background tasks like metrics streaming.
"""

import asyncio
from typing import Optional
from src.services.socket_service import SocketService
from src.services.chromadb_metrics import ChromaDBMetricsCollector
from src.database import DatabaseManager
from src.modules.core import Logger


class BackgroundTaskManager:
    """Manages application background tasks."""

    def __init__(
        self,
        socket_service: SocketService,
        metrics_collector: ChromaDBMetricsCollector,
        db_manager: DatabaseManager,
        logger: Logger,
        interval_seconds: int = 5
    ):
        """
        Initialize background task manager.

        Args:
            socket_service: SocketService instance for emitting events
            metrics_collector: ChromaDBMetricsCollector instance
            db_manager: DatabaseManager instance for database sessions
            logger: Logger instance
            interval_seconds: Metrics update interval in seconds
        """
        self.socket_service = socket_service
        self.metrics_collector = metrics_collector
        self.db_manager = db_manager
        self.logger = logger
        self.interval_seconds = interval_seconds
        self.metrics_task: Optional[asyncio.Task] = None

    async def _stream_metrics_to_clients(self):
        """
        Background task to stream metrics to connected clients via Socket.IO.

        Runs continuously until cancelled, emitting metrics at regular intervals.
        """
        self.logger.info(f"Starting metrics streaming task (interval: {self.interval_seconds}s)")

        try:
            while True:
                try:
                    # Get database session
                    async with self.db_manager.session_factory() as session:
                        # Get metrics snapshot
                        snapshot = await self.metrics_collector.get_snapshot(session)

                        # Emit to all connected clients
                        await self.socket_service.emit_to_all("metrics_update", snapshot)

                        self.logger.debug("Metrics snapshot sent to clients")

                except Exception as e:
                    self.logger.error(f"Error streaming metrics: {e}", exc_info=True)

                # Wait before next update
                await asyncio.sleep(self.interval_seconds)

        except asyncio.CancelledError:
            self.logger.info("Metrics streaming task cancelled")
            raise

    def start_metrics_streaming(self) -> asyncio.Task:
        """
        Start the metrics streaming background task.

        Returns:
            The created asyncio Task
        """
        self.metrics_task = asyncio.create_task(self._stream_metrics_to_clients())
        self.logger.info(f"Metrics streaming task started ({self.interval_seconds}s interval)")
        return self.metrics_task

    async def stop_metrics_streaming(self):
        """Stop the metrics streaming background task gracefully."""
        if self.metrics_task:
            self.metrics_task.cancel()
            try:
                await self.metrics_task
            except asyncio.CancelledError:
                self.logger.info("Metrics streaming task cancelled")
