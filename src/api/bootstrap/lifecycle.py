"""
Application lifecycle management for FastAPI.

Coordinates startup and shutdown sequences including:
- Service initialization
- Background task management
- Event handler setup
- Resource cleanup
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from typing import Optional

from src.database import DatabaseManager
from src.modules.core import Logger, EventBus
from src.services.socket_service import SocketService
from src.services.chromadb_metrics import ChromaDBMetricsCollector
from src.api.bootstrap.config import AppConfig, ServiceConfig
from src.api.bootstrap.services import (
    initialize_llm_service,
    initialize_chromadb_metrics,
    initialize_sxthalamus,
)
from src.api.bootstrap.background_tasks import BackgroundTaskManager


class LifecycleOrchestrator:
    """Orchestrates application startup and shutdown sequences."""

    def __init__(
        self,
        app_config: AppConfig,
        service_config: ServiceConfig,
        event_bus: EventBus,
        logger: Logger,
        socket_service: SocketService,
        embedding_service: Optional[object] = None
    ):
        """
        Initialize lifecycle orchestrator.

        Args:
            app_config: Application configuration
            service_config: Service configuration
            event_bus: EventBus instance
            logger: Logger instance
            socket_service: SocketService instance
            embedding_service: Optional embedding service
        """
        self.app_config = app_config
        self.service_config = service_config
        self.event_bus = event_bus
        self.logger = logger
        self.socket_service = socket_service
        self.embedding_service = embedding_service
        self.background_task_manager: Optional[BackgroundTaskManager] = None

    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        """
        FastAPI lifespan context manager.

        Handles startup and shutdown sequences.
        """
        # Startup
        await self._startup(app)

        yield

        # Shutdown
        await self._shutdown(app)

    async def _startup(self, app: FastAPI):
        """Execute startup sequence."""
        self.logger.info("Application starting...")

        # Attach core services to app state
        self._attach_core_services(app)

        # Initialize database
        self._initialize_database(app)

        # Initialize LLM service
        self._initialize_llm_service(app)

        # Initialize ChromaDB metrics
        chromadb_metrics_collector = self._initialize_chromadb_metrics()
        app.state.chromadb_metrics_collector = chromadb_metrics_collector

        # Start background tasks
        self._start_background_tasks(app, chromadb_metrics_collector)

        # Initialize event handlers
        self._initialize_event_handlers(app)

        # Initialize SXThalamus service
        self._initialize_sxthalamus_service(app)

    async def _shutdown(self, app: FastAPI):
        """Execute shutdown sequence."""
        self.logger.info("Application shutting down...")

        # Stop background tasks
        if self.background_task_manager:
            await self.background_task_manager.stop_metrics_streaming()

        # Close database
        await app.state.db_manager.close()

        # Close SXThalamus service
        if hasattr(app.state, 'sxthalamus_service') and app.state.sxthalamus_service:
            await app.state.sxthalamus_service.close()
            self.logger.info("SXThalamus service closed")

        # Close embedding service
        if self.embedding_service:
            await self.embedding_service.close()
            self.logger.info("Embedding service closed")

    def _attach_core_services(self, app: FastAPI):
        """Attach core services to app state."""
        app.state.event_bus = self.event_bus
        app.state.logger = self.logger
        app.state.socket_service = self.socket_service
        app.state.embedding_service = self.embedding_service

    def _initialize_database(self, app: FastAPI):
        """Initialize database connection."""
        app.state.db_manager = DatabaseManager(self.app_config.database_url)
        self.logger.info("Database connection initialized")
        self.logger.info("Socket.IO service initialized")

    def _initialize_llm_service(self, app: FastAPI):
        """Initialize LLM service."""
        llm_service = initialize_llm_service(app.state.db_manager, self.logger)
        app.state.llm_service = llm_service

    def _initialize_chromadb_metrics(self) -> ChromaDBMetricsCollector:
        """Initialize ChromaDB metrics collector."""
        return initialize_chromadb_metrics(
            self.service_config,
            self.event_bus,
            self.logger
        )

    def _start_background_tasks(self, app: FastAPI, chromadb_metrics_collector: ChromaDBMetricsCollector):
        """Start background tasks like metrics streaming."""
        self.background_task_manager = BackgroundTaskManager(
            socket_service=self.socket_service,
            metrics_collector=chromadb_metrics_collector,
            db_manager=app.state.db_manager,
            logger=self.logger,
            interval_seconds=self.service_config.background_tasks.metrics_interval_seconds
        )

        metrics_task = self.background_task_manager.start_metrics_streaming()
        app.state.metrics_streaming_task = metrics_task

    def _initialize_event_handlers(self, app: FastAPI):
        """Initialize event handlers for memory log storage."""
        if self.embedding_service:
            from src.api.dependencies.event_handlers import initialize_event_handlers
            from src.api.dependencies.vector_storage import initialize_vector_storage_service

            try:
                # Initialize vector storage dependencies (validates configuration)
                initialize_vector_storage_service(
                    self.embedding_service,
                    self.event_bus,
                    self.logger
                )

                # Initialize event handlers with per-project isolation
                # Use db_manager.session_factory instead of get_db_session (which requires Request)
                # Event handlers run as background tasks outside HTTP request/response cycle
                initialize_event_handlers(
                    event_bus=self.event_bus,
                    logger=self.logger,
                    db_session_factory=app.state.db_manager.session_factory,
                    embedding_service=self.embedding_service
                )
                self.logger.info("Event-driven memory log storage initialized (per-project isolation)")
            except Exception as e:
                self.logger.error(f"Failed to initialize event handlers: {e}")
        else:
            self.logger.warning("Event handlers not initialized - embedding service unavailable")

    def _initialize_sxthalamus_service(self, app: FastAPI):
        """Initialize SXThalamus service if enabled."""
        sxthalamus_service = initialize_sxthalamus(
            self.event_bus,
            self.logger,
            app.state.llm_service
        )
        app.state.sxthalamus_service = sxthalamus_service
