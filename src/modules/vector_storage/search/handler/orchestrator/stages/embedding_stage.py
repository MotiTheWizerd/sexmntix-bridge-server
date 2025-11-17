"""
Embedding Stage for Search Workflow

Handles query embedding generation with telemetry logging.
"""

from typing import Any
from src.modules.embeddings import EmbeddingService
from ...telemetry import SearchTelemetry


class EmbeddingStage:
    """
    Stage 1: Generate query embedding.

    Responsibilities:
    - Generate embedding for search query
    - Log embedding generation with telemetry
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        telemetry: SearchTelemetry
    ):
        """
        Initialize the embedding stage.

        Args:
            embedding_service: Service for generating embeddings
            telemetry: Telemetry handler for logging
        """
        self.embedding_service = embedding_service
        self.telemetry = telemetry

    async def execute(self, query: str) -> Any:
        """
        Generate embedding for the search query.

        Args:
            query: The search query text

        Returns:
            Embedding response from the embedding service
        """
        embedding_response = await self.embedding_service.generate_embedding(
            text=query
        )

        self.telemetry.log_embedding_generated(
            len(embedding_response.embedding),
            embedding_response.cached
        )

        return embedding_response
