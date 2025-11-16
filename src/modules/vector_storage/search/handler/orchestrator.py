"""
Search Workflow Orchestrator

Single Responsibility: Orchestrate the multi-step search workflow.

This module coordinates the flow of a search operation through various
stages: embedding generation, vector search, filtering, and reranking.
"""

import time
from typing import List, Dict, Any
from src.modules.embeddings import EmbeddingService
from src.infrastructure.chromadb.repository import VectorRepository
from src.infrastructure.chromadb.models import SearchResult
from ..filters import FilterOrchestrator
from .models import SearchRequest, SearchResponse
from .formatters import format_results_as_dicts
from .telemetry import SearchTelemetry


class SearchWorkflowOrchestrator:
    """
    Orchestrates the complete search workflow.

    Coordinates the interaction between:
    - EmbeddingService (query embedding generation)
    - VectorRepository (similarity search)
    - FilterOrchestrator (result filtering and ranking)
    - SearchTelemetry (logging and events)
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_repository: VectorRepository,
        telemetry: SearchTelemetry
    ):
        """
        Initialize the orchestrator.

        Args:
            embedding_service: Service for generating embeddings
            vector_repository: Repository for ChromaDB operations
            telemetry: Telemetry handler for logging and events
        """
        self.embedding_service = embedding_service
        self.vector_repository = vector_repository
        self.telemetry = telemetry

    async def execute_search(self, request: SearchRequest) -> SearchResponse:
        """
        Execute the complete search workflow.

        Workflow stages:
        1. Log search start
        2. Generate query embedding
        3. Search ChromaDB for similar vectors
        4. Filter by minimum similarity
        5. Apply temporal decay (if enabled)
        6. Format results
        7. Collect metrics and publish events

        Args:
            request: The search request parameters

        Returns:
            SearchResponse with results and metadata
        """
        # Log search start
        self.telemetry.log_search_start(request)
        start_time = time.time()

        # Stage 1: Generate query embedding
        embedding_response = await self._generate_embedding(request.query)

        # Stage 2: Search ChromaDB
        search_results = await self._search_vectors(
            embedding_response.embedding,
            request
        )

        # Stage 3: Filter and rank results
        processed_results = self._process_results(
            search_results,
            request
        )

        # Stage 4: Format and collect metrics
        response = await self._build_response(
            processed_results,
            request,
            start_time,
            embedding_response.cached
        )

        # Stage 5: Publish events
        self.telemetry.publish_all_events(response)
        self.telemetry.log_search_completion(
            response.results_count,
            response.duration_ms,
            request.min_similarity,
            response.query_cached,
            response.collection_size
        )

        return response

    async def _generate_embedding(self, query: str) -> Any:
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

    async def _search_vectors(
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
        self.telemetry.log_chromadb_search(
            request.user_id,
            request.project_id,
            request.limit,
            request.where_filter,
            0  # Will be updated after search
        )

        results = await self.vector_repository.search(
            query_embedding=query_embedding,
            user_id=request.user_id,
            project_id=request.project_id,
            limit=request.limit,
            where_filter=request.where_filter
        )

        self.telemetry.log_chromadb_search(
            request.user_id,
            request.project_id,
            request.limit,
            request.where_filter,
            len(results)
        )

        return results

    def _process_results(
        self,
        results: List[SearchResult],
        request: SearchRequest
    ) -> List[SearchResult]:
        """
        Filter and rank search results.

        Applies:
        1. Minimum similarity filtering
        2. Temporal decay reranking (if enabled)

        Args:
            results: Raw search results
            request: The search request

        Returns:
            Processed search results
        """
        # Filter by minimum similarity
        filtered_results = FilterOrchestrator.filter_by_minimum_similarity(
            results=results,
            min_similarity=request.min_similarity
        )

        # Apply temporal decay reranking (if enabled)
        reranked_results = FilterOrchestrator.apply_temporal_decay(
            results=filtered_results,
            enable_temporal_decay=request.enable_temporal_decay,
            half_life_days=request.half_life_days
        )

        self.telemetry.log_temporal_decay(
            request.enable_temporal_decay,
            request.half_life_days
        )

        return reranked_results

    async def _build_response(
        self,
        results: List[SearchResult],
        request: SearchRequest,
        start_time: float,
        query_cached: bool
    ) -> SearchResponse:
        """
        Build the final search response with metrics.

        Args:
            results: Processed search results
            request: The original search request
            start_time: Search start timestamp
            query_cached: Whether the query embedding was cached

        Returns:
            Complete SearchResponse
        """
        # Convert to dict format
        results_data = format_results_as_dicts(results)

        # Calculate metrics
        duration_ms = (time.time() - start_time) * 1000
        collection_size = await self.vector_repository.count(
            request.user_id,
            request.project_id
        )

        # Build response
        return SearchResponse.from_search_results(
            results=results_data,
            request=request,
            duration_ms=duration_ms,
            collection_size=collection_size,
            query_cached=query_cached
        )
