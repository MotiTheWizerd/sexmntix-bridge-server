"""
Dependency for VectorStorageService injection.
"""

import os
from fastapi import Request
from src.modules.vector_storage import VectorStorageService
from src.modules.embeddings import EmbeddingService
from src.modules.core import EventBus, Logger
from src.infrastructure.chromadb.client import ChromaDBClient
from src.infrastructure.chromadb.repository import VectorRepository


# ChromaDB base path
CHROMADB_BASE_PATH = os.getenv("CHROMADB_PATH", "./data/chromadb")

# Single shared ChromaDB client for all users/projects
# Isolation is achieved via collection naming, not physical separation
_shared_chromadb_client: ChromaDBClient | None = None

# Initialize vector storage service (singleton for embedding service)
_vector_storage_service: VectorStorageService | None = None


def get_chromadb_client(user_id: str = None, project_id: str = None) -> ChromaDBClient:
    """
    Get or create the shared ChromaDB client.

    All users and projects share a single ChromaDB instance. Isolation is
    achieved through collection naming (hash-based), not physical separation.

    Args:
        user_id: Ignored (kept for backward compatibility)
        project_id: Ignored (kept for backward compatibility)

    Returns:
        Shared ChromaDBClient instance
    """
    global _shared_chromadb_client

    # Return cached client if exists
    if _shared_chromadb_client is not None:
        return _shared_chromadb_client

    # Create single shared client at base path
    _shared_chromadb_client = ChromaDBClient(
        storage_path=CHROMADB_BASE_PATH,
        user_id=None,
        project_id=None
    )

    return _shared_chromadb_client


def get_base_chromadb_client() -> ChromaDBClient:
    """
    Get or create the shared ChromaDB client.

    Alias for get_chromadb_client() for backward compatibility.
    Since all clients now share the same instance, this returns the same client.

    Returns:
        Shared ChromaDBClient instance
    """
    return get_chromadb_client()


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

    All users/projects share the same ChromaDB client. Isolation is achieved
    via collection naming within the shared instance.

    Args:
        user_id: User identifier (used for collection naming only)
        project_id: Project identifier (used for collection naming only)
        embedding_service: EmbeddingService instance
        event_bus: EventBus instance
        logger: Logger instance

    Returns:
        VectorStorageService instance with shared ChromaDB client
    """
    # Get shared ChromaDB client (same for all users/projects)
    chromadb_client = get_chromadb_client()

    # Create vector repository with the shared client
    # Isolation happens via collection naming (hash of user_id:project_id)
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
    Create VectorStorageService using shared ChromaDB client.

    Alias for create_vector_storage_service() for backward compatibility.
    Since all clients now share the same instance, this returns the same service.

    Args:
        embedding_service: EmbeddingService instance
        event_bus: EventBus instance
        logger: Logger instance

    Returns:
        VectorStorageService instance with shared ChromaDB client
    """
    # Get shared ChromaDB client
    chromadb_client = get_chromadb_client()

    # Create vector repository with the shared client
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

    Initializes the shared ChromaDB client. All users/projects share the same
    instance with isolation via collection naming.

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

    # Initialize shared ChromaDB client on startup
    get_chromadb_client()

    logger.info("Vector storage dependencies initialized (single shared ChromaDB instance)")


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
