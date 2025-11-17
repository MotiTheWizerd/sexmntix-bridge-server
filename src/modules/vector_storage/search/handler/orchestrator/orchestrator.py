"""
Search Workflow Orchestrator

Lightweight coordinator that delegates to stage classes.
Each stage handles a specific part of the search workflow.
"""

from src.modules.embeddings import EmbeddingService
from src.infrastructure.chromadb.repository import VectorRepository
from ..models import SearchRequest, SearchResponse
from ..telemetry import SearchTelemetry
from .stages.embedding_stage import EmbeddingStage
from .stages.search_stage import SearchStage
from .stages.processing_stage import ProcessingStage
from .stages.response_stage import ResponseStage
from .utils.timing import start_timer, calculate_duration_ms


class SearchWorkflowOrchestrator:
    """
    Orchestrates the complete search workflow using stage classes.

    Workflow:
    1. EmbeddingStage - Generate query embedding
    2. SearchStage - Search ChromaDB for similar vectors
    3. ProcessingStage - Filter and rank results
    4. ResponseStage - Build response with metrics
    5. Telemetry - Log and publish events

    Each stage is isolated and can be tested independently.
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_repository: VectorRepository,
        telemetry: SearchTelemetry
    ):
        """
        Initialize the orchestrator with all required stages.

        Args:
            embedding_service: Service for generating embeddings
            vector_repository: Repository for ChromaDB operations
            telemetry: Telemetry handler for logging and events
        """
        self.telemetry = telemetry

        # Initialize all stages
        self.embedding_stage = EmbeddingStage(embedding_service, telemetry)
        self.search_stage = SearchStage(vector_repository, telemetry)
        self.processing_stage = ProcessingStage(telemetry)
        self.response_stage = ResponseStage(vector_repository)

    async def execute_search(self, request: SearchRequest) -> SearchResponse:
        """
        Execute the complete search workflow through stages.

        Args:
            request: The search request parameters

        Returns:
            SearchResponse with results and metadata
        """
        # Log search start
        self.telemetry.log_search_start(request)
        start_time = start_timer()

        # Stage 1: Generate query embedding
        embedding_response = await self.embedding_stage.execute(request.query)

        # Stage 2: Search ChromaDB
        search_results = await self.search_stage.execute(
            embedding_response.embedding,
            request
        )

        # Stage 3: Filter and rank results
        processed_results = self.processing_stage.execute(
            search_results,
            request
        )

        # Stage 4: Build response with metrics
        duration_ms = calculate_duration_ms(start_time)
        response = await self.response_stage.execute(
            processed_results,
            request,
            duration_ms,
            embedding_response.cached
        )

        # Stage 5: Publish events and log completion
        self.telemetry.publish_all_events(response)
        self.telemetry.log_search_completion(
            response.results_count,
            response.duration_ms,
            request.min_similarity,
            response.query_cached,
            response.collection_size
        )

        return response
