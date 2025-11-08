from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from src.modules.core import EventBus, Logger
from src.database import DatabaseManager
from src.api.middleware.logging import LoggingMiddleware
from src.api.routes import health, memory_logs
import os
from dotenv import load_dotenv

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.event_bus = EventBus()
    app.state.logger = Logger("semantic-bridge-server")
    app.state.logger.info("Application starting...")
    
    database_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/semantic_bridge")
    app.state.db_manager = DatabaseManager(database_url)
    app.state.logger.info("Database connection initialized")
    
    yield
    
    # Shutdown
    app.state.logger.info("Application shutting down...")
    await app.state.db_manager.close()


def create_app() -> FastAPI:
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
    
    return app
