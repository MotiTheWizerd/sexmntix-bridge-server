"""
Search Stage for Search Workflow

Handles vector similarity search in ChromaDB with telemetry logging.
"""

from typing import List
from src.infrastructure.chromadb.repository import VectorRepository
from src.infrastructure.chromadb.models import SearchResult
from ...models import SearchRequest
from ...telemetry import SearchTelemetry


class SearchStage:
    """
    Stage 2: Search for similar vectors in ChromaDB.

    Responsibilities:
    - Execute vector similarity search
    - Log search operations with telemetry
    """

    def __init__(
        self,
        vector_repository: VectorRepository,
        telemetry: SearchTelemetry
    ):
        """
        Initialize the search stage.

        Args:
            vector_repository: Repository for ChromaDB operations
            telemetry: Telemetry handler for logging
        """
        self.vector_repository = vector_repository
        self.telemetry = telemetry

    async def execute(
        self,
        query_embedding: List[float],
        request: SearchRequest
    ) -> List[SearchResult]:
        """
        Search for similar vectors in ChromaDB.

        Args:
            query_embedding: The query embedding vector
            request: The search request

        Returns:
            List of search results from ChromaDB
        """
        # Log search start
        self.telemetry.log_chromadb_search(
            request.user_id,
            request.project_id,
            request.limit,
            request.where_filter,
            0  # Will be updated after search
        )

        # Execute search
        results = await self.vector_repository.search(
            query_embedding=query_embedding,
            user_id=request.user_id,
            project_id=request.project_id,
            limit=request.limit,
            where_filter=request.where_filter,
            collection_prefix=request.collection_prefix,
            min_similarity=request.min_similarity
        )

        # Log search completion
        self.telemetry.log_chromadb_search(
            request.user_id,
            request.project_id,
            request.limit,
            request.where_filter,
            len(results)
        )

        return results
