"""
XCP Server Standalone Entry Point

Run this module to start the XCP/MCP server as a standalone process:
    python -m src.modules.xcp_server

This is the recommended way to run the XCP server for use with Claude Desktop
or other MCP clients.
"""

import asyncio
import sys
import logging
from contextlib import asynccontextmanager

from src.modules.core.event_bus.event_bus import EventBus
from src.modules.core.telemetry.logger import setup_logger
from src.modules.embeddings import EmbeddingService
from src.modules.embeddings.providers.google import GoogleEmbeddingProvider
from src.modules.embeddings.models.config import EmbeddingConfig
from src.modules.embeddings.caching import EmbeddingCache
from src.modules.vector_storage.service import VectorStorageService
from src.infrastructure.chromadb.client import ChromaDBClient
from src.infrastructure.chromadb.repository import VectorRepository
from src.database.connection import DatabaseConnectionManager
from src.modules.xcp_server import XCPServerService
from src.modules.xcp_server.models.config import load_xcp_config
from src.modules.xcp_server.exceptions import XCPServerNotEnabledError


async def main():
    """Main entry point for standalone XCP server"""

    # Load configuration
    config = load_xcp_config()

    # Setup logging
    logger = setup_logger(
        name="xcp_server",
        log_level=config.log_level.value.upper()
    )

    logger.info("=" * 60)
    logger.info(f"Starting {config.server_name} v{config.server_version}")
    logger.info("=" * 60)

    # Check if server is enabled
    if not config.enabled:
        logger.error("XCP server is disabled. Set XCP_SERVER_ENABLED=true in .env")
        sys.exit(1)

    # Initialize Event Bus
    event_bus = EventBus(logger)
    logger.info("Event bus initialized")

    # Initialize Database Connection Manager
    db_manager = DatabaseConnectionManager(logger)
    await db_manager.initialize()
    logger.info("Database connection initialized")

    # Create database session factory
    @asynccontextmanager
    async def db_session_factory():
        async with db_manager.get_session() as session:
            yield session

    # Initialize Embedding Service
    try:
        embedding_config = EmbeddingConfig()
        embedding_provider = GoogleEmbeddingProvider(embedding_config)
        embedding_cache = EmbeddingCache(
            max_size=embedding_config.cache_size,
            ttl_hours=embedding_config.cache_ttl_hours
        )
        embedding_service = EmbeddingService(
            event_bus=event_bus,
            logger=logger,
            provider=embedding_provider,
            cache=embedding_cache,
            cache_enabled=embedding_config.cache_enabled
        )
        logger.info("Embedding service initialized")
    except Exception as e:
        logger.error(f"Failed to initialize embedding service: {e}")
        await db_manager.close()
        sys.exit(1)

    # Initialize ChromaDB
    try:
        chromadb_client = ChromaDBClient(logger)
        vector_repository = VectorRepository(chromadb_client, logger)
        logger.info("ChromaDB client initialized")
    except Exception as e:
        logger.error(f"Failed to initialize ChromaDB: {e}")
        await db_manager.close()
        sys.exit(1)

    # Initialize Vector Storage Service
    vector_storage_service = VectorStorageService(
        event_bus=event_bus,
        logger=logger,
        embedding_service=embedding_service,
        vector_repository=vector_repository
    )
    logger.info("Vector storage service initialized")

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
    logger.info("=" * 60)
    logger.info("Server Configuration:")
    logger.info(f"  Name: {server_info['server_name']}")
    logger.info(f"  Version: {server_info['server_version']}")
    logger.info(f"  Transport: {server_info['transport']}")
    logger.info(f"  Default User ID: {server_info['default_user_id']}")
    logger.info(f"  Default Project ID: {server_info['default_project_id']}")
    logger.info(f"  Registered Tools ({len(server_info['tools'])}):")
    for tool_name in server_info['tools']:
        logger.info(f"    - {tool_name}")
    logger.info("=" * 60)

    try:
        # Start the XCP server (blocking call for stdio)
        logger.info("Starting XCP server (stdio transport)")
        logger.info("Waiting for MCP client connection...")
        await xcp_service.start()

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")

    except XCPServerNotEnabledError:
        logger.error("XCP server is not enabled")
        sys.exit(1)

    except Exception as e:
        logger.exception(f"Server error: {e}")
        sys.exit(1)

    finally:
        # Cleanup
        logger.info("Cleaning up resources...")
        await xcp_service.stop()
        await db_manager.close()
        logger.info("XCP server stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown complete")
        sys.exit(0)
    except Exception as e:
        print(f"\nFatal error: {e}", file=sys.stderr)
        sys.exit(1)
