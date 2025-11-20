from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import asyncio
from contextlib import asynccontextmanager
from src.database import DatabaseManager
from src.api.middleware.logging import LoggingMiddleware
from src.api.routes import health, memory_logs, mental_notes, users, socket_test, memory_logs_example, embeddings, monitoring, conversations, user_projects
from src.api.bootstrap.config import load_app_config, load_service_config
from src.api.bootstrap.services import (
    initialize_core_services,
    initialize_embedding_service,
    initialize_chromadb_metrics,
    initialize_llm_service,
    initialize_sxthalamus,
)
from src.services.socket_service import SocketService
from src.services.chromadb_metrics import ChromaDBMetricsCollector
from src.modules.core import Logger
import socketio
from dotenv import load_dotenv

load_dotenv()

# Load configuration
app_config = load_app_config()
service_config = load_service_config()

# Initialize core services that need to be available before app creation
event_bus, logger, socket_service = initialize_core_services()


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
embedding_service = initialize_embedding_service(service_config, event_bus, logger)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.event_bus = event_bus
    app.state.logger = logger
    app.state.socket_service = socket_service
    app.state.embedding_service = embedding_service
    app.state.logger.info("Application starting...")

    app.state.db_manager = DatabaseManager(app_config.database_url)
    app.state.logger.info("Database connection initialized")
    app.state.logger.info("Socket.IO service initialized")

    # Initialize LLM service
    llm_service = initialize_llm_service(app.state.db_manager, logger)
    app.state.llm_service = llm_service

    # Initialize ChromaDB metrics collector
    chromadb_metrics_collector = initialize_chromadb_metrics(
        service_config, event_bus, logger
    )
    app.state.chromadb_metrics_collector = chromadb_metrics_collector

    # Start background task for streaming metrics to UI
    metrics_streaming_task = asyncio.create_task(
        stream_metrics_to_clients(
            socket_service=socket_service,
            metrics_collector=chromadb_metrics_collector,
            db_manager=app.state.db_manager,
            logger=logger,
            interval_seconds=service_config.background_tasks.metrics_interval_seconds
        )
    )
    app.state.metrics_streaming_task = metrics_streaming_task
    app.state.logger.info(
        f"Metrics streaming task started "
        f"({service_config.background_tasks.metrics_interval_seconds}s interval)"
    )

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

    # Initialize SXThalamus Service (if enabled)
    sxthalamus_service = initialize_sxthalamus(event_bus, logger, llm_service)
    app.state.sxthalamus_service = sxthalamus_service

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
        title=app_config.title,
        description=app_config.description,
        version=app_config.version,
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
        allow_origins=app_config.cors_allow_origins,
        allow_credentials=app_config.cors_allow_credentials,
        allow_methods=app_config.cors_allow_methods,
        allow_headers=app_config.cors_allow_headers,
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
    app.include_router(user_projects.router)

    # Register embeddings router if service is available
    if embedding_service:
        app.include_router(embeddings.router)

    # Mount Socket.IO
    app.mount("/socket.io", socket_app)

    return app
