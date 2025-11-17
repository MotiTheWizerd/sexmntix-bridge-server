from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import asyncio
from contextlib import asynccontextmanager
from src.modules.core import EventBus, Logger
from src.database import DatabaseManager
from src.api.middleware.logging import LoggingMiddleware
from src.api.routes import health, memory_logs, mental_notes, users, socket_test, memory_logs_example, embeddings, monitoring, conversations
from src.services.socket_service import SocketService
from src.services.chromadb_metrics import ChromaDBMetricsCollector
from src.events.emitters import EventEmitter
from src.infrastructure.chromadb.client import ChromaDBClient
from src.modules.embeddings import (
    EmbeddingService,
    GoogleEmbeddingProvider,
    ProviderConfig,
    EmbeddingCache,
)
import socketio
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize services that need to be available before app creation
event_bus = EventBus()
logger = Logger("semantic-bridge-server")
socket_service = SocketService(event_bus, logger)
event_emitter = EventEmitter(socket_service)


async def stream_metrics_to_clients(
    socket_service: SocketService,
    metrics_collector: ChromaDBMetricsCollector,
    db_manager: DatabaseManager,
    logger: Logger,
    interval_seconds: int = 5
):
    """
    Background task to stream metrics to connected clients via Socket.IO.

    Args:
        socket_service: SocketService instance
        metrics_collector: ChromaDBMetricsCollector instance
        db_manager: DatabaseManager instance
        logger: Logger instance
        interval_seconds: Update interval in seconds
    """
    logger.info(f"Starting metrics streaming task (interval: {interval_seconds}s)")

    try:
        while True:
            try:
                # Get database session
                async with db_manager.session_factory() as session:
                    # Get metrics snapshot
                    snapshot = await metrics_collector.get_snapshot(session)

                    # Emit to all connected clients
                    await socket_service.emit_to_all("metrics_update", snapshot)

                    logger.debug("Metrics snapshot sent to clients")

            except Exception as e:
                logger.error(f"Error streaming metrics: {e}", exc_info=True)

            # Wait before next update
            await asyncio.sleep(interval_seconds)

    except asyncio.CancelledError:
        logger.info("Metrics streaming task cancelled")
        raise

# Initialize embedding service
google_api_key = os.getenv("GOOGLE_API_KEY")
if google_api_key:
    embedding_config = ProviderConfig(
        provider_name="google",
        model_name=os.getenv("EMBEDDING_MODEL", "models/text-embedding-004"),
        api_key=google_api_key,
        timeout_seconds=float(os.getenv("EMBEDDING_TIMEOUT", "30.0")),
        max_retries=int(os.getenv("EMBEDDING_MAX_RETRIES", "3"))
    )
    embedding_provider = GoogleEmbeddingProvider(embedding_config)
    embedding_cache = EmbeddingCache(
        max_size=int(os.getenv("EMBEDDING_CACHE_SIZE", "1000")),
        ttl_hours=int(os.getenv("EMBEDDING_CACHE_TTL_HOURS", "24"))
    )
    embedding_service = EmbeddingService(
        event_bus=event_bus,
        logger=logger,
        provider=embedding_provider,
        cache=embedding_cache,
        cache_enabled=os.getenv("EMBEDDING_CACHE_ENABLED", "true").lower() == "true"
    )
    logger.info("Embedding service initialized successfully")
else:
    embedding_service = None
    logger.warning("GOOGLE_API_KEY not found - embedding service disabled")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.event_bus = event_bus
    app.state.logger = logger
    app.state.socket_service = socket_service
    app.state.event_emitter = event_emitter
    app.state.embedding_service = embedding_service
    app.state.logger.info("Application starting...")

    database_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/semantic_bridge")
    app.state.db_manager = DatabaseManager(database_url)
    app.state.logger.info("Database connection initialized")
    app.state.logger.info("Socket.IO service initialized")

    # Initialize ChromaDB client for metrics (base path, no user/project isolation)
    chromadb_base_path = os.getenv("CHROMADB_PATH", "./data/chromadb")
    chromadb_client = ChromaDBClient(
        storage_path=chromadb_base_path,
        user_id=None,
        project_id=None
    )
    app.state.logger.info(f"ChromaDB client initialized at {chromadb_base_path} (no user/project nesting)")

    # Initialize ChromaDB metrics collector
    chromadb_metrics_collector = ChromaDBMetricsCollector(
        event_bus=event_bus,
        logger=logger,
        chromadb_client=chromadb_client
    )
    app.state.chromadb_metrics_collector = chromadb_metrics_collector
    app.state.logger.info("ChromaDB metrics collector initialized")

    # Start background task for streaming metrics to UI
    metrics_streaming_task = asyncio.create_task(
        stream_metrics_to_clients(
            socket_service=socket_service,
            metrics_collector=chromadb_metrics_collector,
            db_manager=app.state.db_manager,
            logger=logger,
            interval_seconds=5  # Update every 5 seconds
        )
    )
    app.state.metrics_streaming_task = metrics_streaming_task
    app.state.logger.info("Metrics streaming task started (5s interval)")

    # Initialize event handlers for memory log storage
    if embedding_service:
        from src.api.dependencies.event_handlers import initialize_event_handlers
        from src.api.dependencies.vector_storage import initialize_vector_storage_service
        from src.api.dependencies.database import get_db_session

        try:
            # Initialize vector storage dependencies (validates configuration)
            initialize_vector_storage_service(
                embedding_service, event_bus, logger
            )

            # Initialize event handlers with per-project isolation
            initialize_event_handlers(
                event_bus=event_bus,
                logger=logger,
                db_session_factory=get_db_session,
                embedding_service=embedding_service
            )
            logger.info("Event-driven memory log storage initialized (per-project isolation)")
        except Exception as e:
            logger.error(f"Failed to initialize event handlers: {e}")
    else:
        logger.warning("Event handlers not initialized - embedding service unavailable")

    # Initialize XCP Server Service (if enabled)
    from src.modules.xcp_server import XCPServerService
    from src.modules.xcp_server.models.config import load_xcp_config
    from src.events.schemas import EventType
    from datetime import datetime

    xcp_config = load_xcp_config()

    if xcp_config.enabled and embedding_service:
        try:
            from src.api.dependencies.vector_storage import create_base_vector_storage_service
            from src.api.dependencies.database import get_db_session

            logger.info("Initializing XCP MCP Server...")

            # Create base vector storage service (no user/project nesting)
            # XCP server uses base ChromaDB path: data/chromadb/
            vector_storage_service = create_base_vector_storage_service(
                embedding_service=embedding_service,
                event_bus=event_bus,
                logger=logger
            )

            # Initialize XCP Server Service
            xcp_service = XCPServerService(
                event_bus=event_bus,
                logger=logger,
                embedding_service=embedding_service,
                vector_storage_service=vector_storage_service,
                db_session_factory=get_db_session,
                config=xcp_config
            )

            # Initialize XCP server
            xcp_service.initialize()
            app.state.xcp_server_service = xcp_service

            # Emit initialization event with simple timestamp payload
            event_bus.publish(
                EventType.MCP_SERVERS_INITIALIZED.value,
                {"ts": datetime.utcnow().isoformat()}
            )

            logger.info("initialize_mcp_servers event emitted")

        except Exception as e:
            logger.error(f"Failed to initialize XCP server: {e}", exc_info=True)
            app.state.xcp_server_service = None
    else:
        if not xcp_config.enabled:
            logger.info("XCP server disabled in configuration")
        elif not embedding_service:
            logger.warning("XCP server not initialized - embedding service unavailable")
        app.state.xcp_server_service = None

    # Initialize SXThalamus Service (if enabled)
    from src.modules.SXThalamus import SXThalamusService, SXThalamusConfig

    sxthalamus_config = SXThalamusConfig.from_env()

    if sxthalamus_config.enabled:
        try:
            logger.info("Initializing SXThalamus service...")

            sxthalamus_service = SXThalamusService(
                event_bus=event_bus,
                logger=logger,
                config=sxthalamus_config
            )

            # Subscribe to conversation.stored event
            event_bus.subscribe(
                "conversation.stored",
                sxthalamus_service.handle_conversation_stored
            )

            app.state.sxthalamus_service = sxthalamus_service
            logger.info("SXThalamus service initialized and subscribed to conversation.stored")

        except Exception as e:
            logger.error(f"Failed to initialize SXThalamus: {e}", exc_info=True)
            app.state.sxthalamus_service = None
    else:
        logger.info("SXThalamus service disabled in configuration")
        app.state.sxthalamus_service = None

    yield

    # Shutdown
    app.state.logger.info("Application shutting down...")

    # Cancel metrics streaming task
    if hasattr(app.state, 'metrics_streaming_task'):
        app.state.metrics_streaming_task.cancel()
        try:
            await app.state.metrics_streaming_task
        except asyncio.CancelledError:
            app.state.logger.info("Metrics streaming task cancelled")

    await app.state.db_manager.close()

    # Close SXThalamus service if available
    if hasattr(app.state, 'sxthalamus_service') and app.state.sxthalamus_service:
        await app.state.sxthalamus_service.close()
        app.state.logger.info("SXThalamus service closed")

    # Close embedding service if available
    if embedding_service:
        await embedding_service.close()
        app.state.logger.info("Embedding service closed")


def create_app() -> FastAPI:
    # Create Socket.IO ASGI app first
    socket_app = socketio.ASGIApp(socket_service.sio, other_asgi_app=None)

    app = FastAPI(
        title="Semantic Bridge Server",
        description="Event-driven API server",
        version="0.1.0",
        lifespan=lifespan
    )

    # Custom exception handler for validation errors
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        # Log detailed validation errors
        logger.error(f"Validation error on {request.method} {request.url.path}")
        logger.error(f"Validation errors: {exc.errors()}")

        # Try to get request body for debugging
        try:
            body = await request.body()
            logger.error(f"Request body: {body.decode('utf-8')}")
        except Exception as e:
            logger.error(f"Could not read request body: {e}")

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": exc.errors(),
                "body": str(exc.body) if hasattr(exc, 'body') else None
            }
        )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add middleware
    app.add_middleware(LoggingMiddleware)

    # Register routes
    app.include_router(health.router)
    app.include_router(memory_logs.router)
    app.include_router(mental_notes.router)
    app.include_router(conversations.router)
    app.include_router(users.router)
    app.include_router(socket_test.router)
    app.include_router(memory_logs_example.router)
    app.include_router(monitoring.router)

    # Register embeddings router if service is available
    if embedding_service:
        app.include_router(embeddings.router)

    # Mount Socket.IO
    app.mount("/socket.io", socket_app)

    return app
