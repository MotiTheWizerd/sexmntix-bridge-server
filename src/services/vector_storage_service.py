"""
Vector Storage Service

Orchestrates embedding generation and vector storage in ChromaDB.
Integrates EmbeddingService with VectorRepository for semantic search capabilities.
"""

from typing import List, Dict, Any, Optional
from src.services.base_service import BaseService
from src.modules.core import EventBus, Logger
from src.modules.embeddings.service import EmbeddingService
from src.infrastructure.chromadb.repository import VectorRepository, SearchResult


class VectorStorageService(BaseService):
    """
    Service for managing vector embeddings and semantic search.

    Combines:
    - EmbeddingService: Text → Vector generation with caching
    - VectorRepository: Vector storage and similarity search in ChromaDB

    Features:
    - Automatic embedding generation from text
    - Dual storage: PostgreSQL + ChromaDB
    - Semantic search with similarity scoring
    - Event-driven architecture
    """

    def __init__(
        self,
        event_bus: EventBus,
        logger: Logger,
        embedding_service: EmbeddingService,
        vector_repository: VectorRepository
    ):
        """
        Initialize vector storage service.

        Args:
            event_bus: Event bus for publishing domain events
            logger: Logger instance
            embedding_service: Service for generating embeddings
            vector_repository: Repository for ChromaDB operations
        """
        super().__init__(event_bus, logger)
        self.embedding_service = embedding_service
        self.vector_repository = vector_repository

        self.logger.info("VectorStorageService initialized")

    def _register_handlers(self):
        """Register event handlers if needed."""
        pass

    def _extract_searchable_text(self, memory_data: Dict[str, Any]) -> str:
        """
        Extract searchable text from memory log data.

        Combines multiple fields for rich semantic context:
        - task: Main task description
        - summary: High-level summary
        - solution: Implementation details
        - tags: Keywords

        Args:
            memory_data: Memory log data dictionary

        Returns:
            Combined searchable text string
        """
        parts = []

        # Core fields
        if "task" in memory_data:
            parts.append(memory_data["task"])

        if "summary" in memory_data:
            parts.append(memory_data["summary"])

        if "solution" in memory_data:
            solution = memory_data["solution"]
            if isinstance(solution, dict):
                # Handle nested solution object
                if "approach" in solution:
                    parts.append(solution["approach"])
                if "key_changes" in solution and isinstance(solution["key_changes"], list):
                    parts.extend(solution["key_changes"][:5])  # Limit to first 5
            elif isinstance(solution, str):
                parts.append(solution)

        # Tags
        if "tags" in memory_data and isinstance(memory_data["tags"], list):
            parts.append(" ".join(memory_data["tags"]))

        # Component
        if "component" in memory_data:
            parts.append(memory_data["component"])

        # Root cause
        if "root_cause" in memory_data:
            parts.append(memory_data["root_cause"])

        # Combine with spaces
        searchable_text = " ".join(parts)

        return searchable_text.strip()

    async def store_memory_vector(
        self,
        memory_log_id: int,
        memory_data: Dict[str, Any],
        user_id: str,
        project_id: str,
        text_override: Optional[str] = None
    ) -> tuple[str, List[float]]:
        """
        Generate embedding and store in ChromaDB.

        Workflow:
        1. Extract searchable text from memory data
        2. Generate embedding via EmbeddingService
        3. Store vector in ChromaDB via VectorRepository
        4. Publish event

        Args:
            memory_log_id: Database ID of memory log
            memory_data: Complete memory log data
            user_id: User identifier for collection isolation
            project_id: Project identifier for collection isolation
            text_override: Optional text to embed (overrides extraction)

        Returns:
            Tuple of (memory_id, embedding_vector)

        Raises:
            InvalidTextError: If searchable text is empty
            ProviderError: If embedding generation fails
        """
        # Extract or use provided text
        searchable_text = text_override or self._extract_searchable_text(memory_data)

        if not searchable_text:
            self.logger.warning(f"No searchable text for memory_log_id: {memory_log_id}")
            searchable_text = memory_data.get("task", "untitled")

        self.logger.info(
            f"Generating embedding for memory_log {memory_log_id} "
            f"(user: {user_id}, project: {project_id})"
        )

        # Generate embedding
        embedding_response = await self.embedding_service.generate_embedding(
            text=searchable_text
        )

        embedding = embedding_response.embedding

        # Store in ChromaDB
        memory_id = await self.vector_repository.add_memory(
            memory_log_id=memory_log_id,
            embedding=embedding,
            memory_data=memory_data,
            user_id=user_id,
            project_id=project_id
        )

        # Publish event
        self.event_bus.publish("vector.stored", {
            "memory_id": memory_id,
            "memory_log_id": memory_log_id,
            "user_id": user_id,
            "project_id": project_id,
            "embedding_dim": len(embedding),
            "cached": embedding_response.cached
        })

        self.logger.info(
            f"Vector stored: {memory_id} "
            f"(dim: {len(embedding)}, cached: {embedding_response.cached})"
        )

        return memory_id, embedding

    async def search_similar_memories(
        self,
        query: str,
        user_id: str,
        project_id: str,
        limit: int = 10,
        where_filter: Optional[Dict[str, Any]] = None,
        min_similarity: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Semantic search for similar memories.

        Workflow:
        1. Generate embedding for query text
        2. Search ChromaDB for similar vectors
        3. Convert L2 distance to similarity percentage
        4. Filter by minimum similarity threshold
        5. Publish event

        Args:
            query: Search query text
            user_id: User identifier for collection isolation
            project_id: Project identifier for collection isolation
            limit: Maximum number of results
            where_filter: Optional metadata filter (ChromaDB where syntax)
            min_similarity: Minimum similarity threshold (0.0 to 1.0)

        Returns:
            List of search results with similarity scores

        Example:
            results = await service.search_similar_memories(
                query="authentication bug fix",
                user_id="user123",
                project_id="project456",
                limit=5,
                min_similarity=0.5
            )
        """
        self.logger.info(
            f"Searching memories for query: '{query[:100]}...' "
            f"(user: {user_id}, project: {project_id})"
        )

        # Generate query embedding
        embedding_response = await self.embedding_service.generate_embedding(
            text=query
        )

        query_embedding = embedding_response.embedding

        # Search ChromaDB
        search_results = await self.vector_repository.search(
            query_embedding=query_embedding,
            user_id=user_id,
            project_id=project_id,
            limit=limit,
            where_filter=where_filter
        )

        # Filter by minimum similarity
        filtered_results = [
            result for result in search_results
            if result.similarity >= min_similarity
        ]

        # Convert to dict format
        results_data = [result.to_dict() for result in filtered_results]

        # Publish event
        self.event_bus.publish("vector.searched", {
            "query": query[:100],
            "user_id": user_id,
            "project_id": project_id,
            "results_count": len(results_data),
            "query_cached": embedding_response.cached
        })

        self.logger.info(
            f"Found {len(results_data)} memories "
            f"(min_similarity: {min_similarity}, cached: {embedding_response.cached})"
        )

        return results_data

    async def get_memory(
        self,
        memory_id: str,
        user_id: str,
        project_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve specific memory by ID.

        Args:
            memory_id: Memory identifier
            user_id: User identifier
            project_id: Project identifier

        Returns:
            Memory document dict or None if not found
        """
        return await self.vector_repository.get_by_id(
            memory_id=memory_id,
            user_id=user_id,
            project_id=project_id
        )

    async def delete_memory(
        self,
        memory_id: str,
        user_id: str,
        project_id: str
    ) -> bool:
        """
        Delete memory from ChromaDB.

        Args:
            memory_id: Memory identifier
            user_id: User identifier
            project_id: Project identifier

        Returns:
            True if deleted, False if not found
        """
        deleted = await self.vector_repository.delete(
            memory_id=memory_id,
            user_id=user_id,
            project_id=project_id
        )

        if deleted:
            self.event_bus.publish("vector.deleted", {
                "memory_id": memory_id,
                "user_id": user_id,
                "project_id": project_id
            })

        return deleted

    async def count_memories(
        self,
        user_id: str,
        project_id: str
    ) -> int:
        """
        Count memories in user/project collection.

        Args:
            user_id: User identifier
            project_id: Project identifier

        Returns:
            Number of memories
        """
        return await self.vector_repository.count(user_id, project_id)
