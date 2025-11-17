"""
Dependency for VectorStorageService injection.
"""

import os
from typing import Dict
from fastapi import Request
from src.modules.vector_storage import VectorStorageService
from src.modules.embeddings import EmbeddingService
from src.modules.core import EventBus, Logger
from src.infrastructure.chromadb.client import ChromaDBClient
from src.infrastructure.chromadb.repository import VectorRepository


# ChromaDB base path
CHROMADB_BASE_PATH = os.getenv("CHROMADB_PATH", "./data/chromadb")

# Cache for ChromaDB clients per user/project (for performance)
_chromadb_clients: Dict[str, ChromaDBClient] = {}

# Cache for base ChromaDB client (no user/project isolation)
_base_chromadb_client: ChromaDBClient | None = None

# Initialize vector storage service (singleton for embedding service)
_vector_storage_service: VectorStorageService | None = None


def get_base_chromadb_client() -> ChromaDBClient:
    """
    Get or create a base ChromaDB client without user/project isolation.

    This is used for server-side operations (like XCP server) that don't need
    per-user/per-project isolation. Uses the base ChromaDB path directly.

    Returns:
        ChromaDBClient instance for base path (no nesting)
    """
    global _base_chromadb_client

    # Return cached client if exists
    if _base_chromadb_client is not None:
        return _base_chromadb_client

    # Create new client at base path (no user_id/project_id)
    _base_chromadb_client = ChromaDBClient(
        storage_path=CHROMADB_BASE_PATH,
        user_id=None,
        project_id=None
    )

    return _base_chromadb_client


def get_chromadb_client(user_id: str, project_id: str) -> ChromaDBClient:
    """
    Get or create a ChromaDB client for specific user/project.

    Implements client caching for performance - each unique user/project
    combination gets its own isolated ChromaDB instance.

    Args:
        user_id: User identifier
        project_id: Project identifier

    Returns:
        ChromaDBClient instance for the user/project
    """
    # Create cache key
    cache_key = f"{user_id}:{project_id}"

    # Return cached client if exists
    if cache_key in _chromadb_clients:
        return _chromadb_clients[cache_key]

    # Create new client with nested path: data/chromadb/{user_id}/{project_id}/
    client = ChromaDBClient(
        storage_path=CHROMADB_BASE_PATH,
        user_id=user_id,
        project_id=project_id
    )

    # Cache for future requests
    _chromadb_clients[cache_key] = client

    return client


def _create_vector_storage_service(
    embedding_service: EmbeddingService,
    event_bus: EventBus,
    logger: Logger,
    vector_repository: VectorRepository
) -> VectorStorageService:
    """
    Create VectorStorageService instance.

    Args:
        embedding_service: EmbeddingService instance
        event_bus: EventBus instance
        logger: Logger instance
        vector_repository: VectorRepository instance

    Returns:
        VectorStorageService instance
    """
    return VectorStorageService(
        event_bus=event_bus,
        logger=logger,
        embedding_service=embedding_service,
        vector_repository=vector_repository
    )


def create_vector_storage_service(
    user_id: str,
    project_id: str,
    embedding_service: EmbeddingService,
    event_bus: EventBus,
    logger: Logger
) -> VectorStorageService:
    """
    Create VectorStorageService for specific user/project.

    This function creates an isolated VectorStorageService with its own
    ChromaDB client pointing to data/chromadb/{user_id}/{project_id}/

    Args:
        user_id: User identifier
        project_id: Project identifier
        embedding_service: EmbeddingService instance
        event_bus: EventBus instance
        logger: Logger instance

    Returns:
        VectorStorageService instance for the user/project
    """
    # Get or create ChromaDB client for this user/project
    chromadb_client = get_chromadb_client(user_id, project_id)

    # Create vector repository with the isolated client
    vector_repository = VectorRepository(chromadb_client)

    # Create vector storage service
    return _create_vector_storage_service(
        embedding_service=embedding_service,
        event_bus=event_bus,
        logger=logger,
        vector_repository=vector_repository
    )


def create_base_vector_storage_service(
    embedding_service: EmbeddingService,
    event_bus: EventBus,
    logger: Logger
) -> VectorStorageService:
    """
    Create VectorStorageService using base ChromaDB path (no user/project isolation).

    This is used for server-side operations (like XCP server) that don't need
    per-user/per-project isolation. Uses data/chromadb/ directly.

    Args:
        embedding_service: EmbeddingService instance
        event_bus: EventBus instance
        logger: Logger instance

    Returns:
        VectorStorageService instance for base path
    """
    # Get or create base ChromaDB client (no nesting)
    chromadb_client = get_base_chromadb_client()

    # Create vector repository with the base client
    vector_repository = VectorRepository(chromadb_client)

    # Create vector storage service
    return _create_vector_storage_service(
        embedding_service=embedding_service,
        event_bus=event_bus,
        logger=logger,
        vector_repository=vector_repository
    )


def initialize_vector_storage_service(
    embedding_service: EmbeddingService,
    event_bus: EventBus,
    logger: Logger
) -> None:
    """
    Initialize vector storage dependencies during app startup.

    Note: With per-project isolation, VectorStorageService instances are
    created on-demand per request. This function just validates dependencies.

    Args:
        embedding_service: EmbeddingService instance
        event_bus: EventBus instance
        logger: Logger instance
    """
    if embedding_service is None:
        raise RuntimeError(
            "EmbeddingService not available. "
            "Ensure GOOGLE_API_KEY is configured in .env"
        )

    # Store references for later use (event handlers, etc.)
    # No longer creating singleton VectorStorageService
    logger.info("Vector storage dependencies initialized (per-project isolation enabled)")


def get_vector_storage_service(
    request: Request,
    user_id: str,
    project_id: str
) -> VectorStorageService:
    """
    Get VectorStorageService instance as FastAPI dependency.

    Creates an isolated VectorStorageService for the specific user/project.

    Args:
        request: FastAPI request object
        user_id: User identifier from request
        project_id: Project identifier from request

    Returns:
        VectorStorageService instance for the user/project

    Raises:
        RuntimeError: If embedding service not available
    """
    embedding_service = request.app.state.embedding_service
    event_bus = request.app.state.event_bus
    logger = request.app.state.logger

    if embedding_service is None:
        raise RuntimeError(
            "EmbeddingService not available. "
            "Ensure GOOGLE_API_KEY is configured in .env"
        )

    # Create service for this specific user/project
    return create_vector_storage_service(
        user_id=user_id,
        project_id=project_id,
        embedding_service=embedding_service,
        event_bus=event_bus,
        logger=logger
    )
