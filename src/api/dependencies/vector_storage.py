"""
Dependency for VectorStorageService injection.
"""

import os
from src.services.vector_storage_service import VectorStorageService
from src.infrastructure.chromadb.client import ChromaDBClient
from src.infrastructure.chromadb.repository import VectorRepository
from src.api.dependencies.embedding import get_embedding_service


# Initialize ChromaDB client (singleton)
CHROMADB_PATH = os.getenv("CHROMADB_PATH", "./data/chromadb")
_chromadb_client = ChromaDBClient(storage_path=CHROMADB_PATH)
_vector_repository = VectorRepository(_chromadb_client)

# Initialize vector storage service (singleton)
_vector_storage_service: VectorStorageService | None = None


def get_vector_storage_service() -> VectorStorageService:
    """
    Get or create VectorStorageService instance.

    Returns:
        VectorStorageService instance

    Raises:
        RuntimeError: If embedding service is not available
    """
    global _vector_storage_service

    if _vector_storage_service is None:
        # Get embedding service
        embedding_service = get_embedding_service()

        if embedding_service is None:
            raise RuntimeError(
                "EmbeddingService not available. "
                "Ensure GOOGLE_API_KEY is configured in .env"
            )

        # Import dependencies
        from src.api.dependencies.event_bus import get_event_bus
        from src.api.dependencies.logger import get_logger

        # Create vector storage service
        _vector_storage_service = VectorStorageService(
            event_bus=get_event_bus(),
            logger=get_logger(),
            embedding_service=embedding_service,
            vector_repository=_vector_repository
        )

    return _vector_storage_service
