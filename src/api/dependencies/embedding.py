"""
Dependency injection for embedding service.
"""

from fastapi import Request
from src.modules.embeddings import EmbeddingService


def get_embedding_service(request: Request) -> EmbeddingService:
    """
    Get the embedding service instance from application state.

    Args:
        request: FastAPI request object

    Returns:
        EmbeddingService instance
    """
    return request.app.state.embedding_service
