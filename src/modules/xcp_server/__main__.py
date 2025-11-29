"""
XCP Server Standalone Entry Point

Run this module to start the XCP/MCP server as a standalone process:
    poetry run python -m src.modules.xcp_server

This is the recommended way to run the XCP server for use with Claude Code or Claude Desktop.
"""

import asyncio
import sys
import os
from pathlib import Path
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load .env from the project root (where this code lives)
# This ensures .env is found even when MCP server is called from other projects
# Path: __main__.py -> xcp_server/ -> modules/ -> src/ -> project_root/
project_root = Path(__file__).parent.parent.parent.parent
dotenv_path = project_root / ".env"
load_dotenv(dotenv_path=dotenv_path, override=False)  # Preserve env vars from .mcp.json

# Import after loading env
from src.modules.core import EventBus, Logger
from src.database import DatabaseManager
from src.modules.embeddings import (
    EmbeddingService,
    GoogleEmbeddingProvider,
    ProviderConfig,
    EmbeddingCache,
)
from src.infrastructure.chromadb.client import ChromaDBClient
from src.infrastructure.chromadb.repository import VectorRepository
from src.modules.vector_storage.service import VectorStorageService
from src.modules.xcp_server import XCPServerService
from src.modules.xcp_server.models.config import load_xcp_config
from src.modules.xcp_server.exceptions import XCPServerNotEnabledError
from src.api.dependencies.event_handlers import initialize_event_handlers


async def main():
    """Main entry point for standalone XCP server"""

    # Load configuration
    config = load_xcp_config()

    # Setup logging
    logger = Logger("xcp_server")

    # logger.info("=" * 60)
    # logger.info(f"Starting {config.server_name} v{config.server_version}")
    # logger.info("=" * 60)

    # Check if server is enabled
    if not config.enabled:
        logger.error("XCP server is disabled. Set XCP_SERVER_ENABLED=true in .env")
        sys.exit(1)

    # Initialize Event Bus
    event_bus = EventBus()
    # logger.info("Event bus initialized")

    # Initialize Database
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL not set in environment")
        sys.exit(1)

    db_manager = DatabaseManager(database_url)
    # logger.info("Database connection initialized")

    # Create async context manager factory for database sessions
    @asynccontextmanager
    async def db_session_factory():
        async for session in db_manager.get_session():
            yield session

    # Initialize Embedding Service
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        logger.error("GOOGLE_API_KEY not set in environment")
        await db_manager.close()
        sys.exit(1)
   
    try:
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
        # logger.info("Embedding service initialized")
    except Exception as e:
        logger.error(f"Failed to initialize embedding service: {e}")
        await db_manager.close()
        sys.exit(1)
    
    # Initialize ChromaDB
    try:
        # Use absolute path for ChromaDB to work from any project
        chromadb_path = os.getenv("CHROMADB_PATH")
        if not chromadb_path:
           
            chromadb_path = str(project_root / "data" / "chromadb")
        print("sds")
        chromadb_client = ChromaDBClient(storage_path=chromadb_path)
        vector_repository = VectorRepository(chromadb_client)
        # logger.info("ChromaDB client initialized")
       
    except Exception as e:
        logger.error(f"Failed to initialize ChromaDB: {e}")
        await db_manager.close()
        print("here")  
        sys.exit(1)
   
    # Initialize Vector Storage Service
    vector_storage_service = VectorStorageService(
        event_bus=event_bus,
        logger=logger,
        embedding_service=embedding_service,
        vector_repository=vector_repository
    )
    # logger.info("Vector storage service initialized")
   
    # Initialize event handlers for background vector storage
    initialize_event_handlers(
        event_bus=event_bus,
        logger=logger,
        db_session_factory=db_session_factory,
        embedding_service=embedding_service
    )
    # logger.info("Event handlers initialized for background vector storage")
  
    # Initialize XCP Server Service
    xcp_service = XCPServerService(
        event_bus=event_bus,
        logger=logger,
        embedding_service=embedding_service,
        vector_storage_service=vector_storage_service,
        db_session_factory=db_session_factory,
        config=config
    )

    # Initialize XCP server
    xcp_service.initialize()

    # Display server info
    server_info = xcp_service.get_server_info()
    # logger.info("=" * 60)
    # logger.info("Server Configuration:")
    # logger.info(f"  Name: {server_info['server_name']}")
    # logger.info(f"  Version: {server_info['server_version']}")
    # logger.info(f"  Transport: {server_info['transport']}")
    # logger.info(f"  Registered Tools ({len(server_info['tools'])}):")
    # for tool_name in server_info['tools']:
    #     logger.info(f"    - {tool_name}")
    # # logger.info("=" * 60)

    try:
        # Start the XCP server (blocking call for stdio)
        # logger.info(f"Starting XCP server ({config.transport} transport)")
        # logger.info("Waiting for MCP client connection...")
        await xcp_service.start()

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")

    except XCPServerNotEnabledError:
        logger.error("XCP server is not enabled")
        sys.exit(1)

    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=e)
        sys.exit(1)

    finally:
        # Cleanup
        # logger.info("Cleaning up resources...")
        await xcp_service.stop()
        await db_manager.close()
        # logger.info("XCP server stopped")


def cli_main():
    """Entry point for the semantic-bridge-mcp command"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown complete")
        sys.exit(0)
    except Exception as e:
        print(f"\nFatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    cli_main()
