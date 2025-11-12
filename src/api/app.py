from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from src.modules.core import EventBus, Logger
from src.database import DatabaseManager
from src.api.middleware.logging import LoggingMiddleware
from src.api.routes import health, memory_logs, mental_notes, users, socket_test, memory_logs_example, embeddings
from src.services.socket_service import SocketService
from src.events.emitters import EventEmitter
from src.modules.embeddings import EmbeddingService
from src.modules.embeddings.provider import GoogleEmbeddingProvider
from src.modules.embeddings.models import ProviderConfig
from src.modules.embeddings.cache import EmbeddingCache
import socketio
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize services that need to be available before app creation
event_bus = EventBus()
logger = Logger("semantic-bridge-server")
socket_service = SocketService(event_bus, logger)
event_emitter = EventEmitter(socket_service)

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

    yield

    # Shutdown
    app.state.logger.info("Application shutting down...")
    await app.state.db_manager.close()

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
    app.include_router(users.router)
    app.include_router(socket_test.router)
    app.include_router(memory_logs_example.router)

    # Register embeddings router if service is available
    if embedding_service:
        app.include_router(embeddings.router)
    
    # Mount Socket.IO
    app.mount("/socket.io", socket_app)
    
    return app
