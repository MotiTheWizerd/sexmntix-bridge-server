"""
Vector Repository for ChromaDB Operations

Orchestrates storage, retrieval, and semantic search of vector embeddings.
Based on TypeScript architecture from 03-chromadb-storage.md.

Operations:
- add_memory: Store vector with metadata
- search: Semantic similarity search
- get_by_id: Retrieve specific memory
- delete: Remove memory from collection
"""

from typing import List, Optional, Dict, Any

from .client import ChromaDBClient
from .models import SearchResult
from .operations import memory, search_operations
from src.modules.core.telemetry.logger import get_logger


class VectorRepository:
    """
    Repository for vector storage and semantic search operations.

    Features:
    - Store embeddings with metadata
    - Semantic similarity search
    - Metadata filtering
    - HNSW index management
    - L2 distance to similarity conversion
    """

    def __init__(self, client: ChromaDBClient):
        """
        Initialize vector repository.

        Args:
            client: ChromaDB client instance
        """
        self.client = client
        self.logger = get_logger(__name__)

    async def add_memory(
        self,
        memory_log_id: int,
        embedding: List[float],
        memory_data: Dict[str, Any],
        user_id: str,
        project_id: str
    ) -> str:
        """
        Add memory embedding to ChromaDB collection.

        Stores 4 components:
        1. ID: Unique identifier
        2. Embedding: 768-dimensional vector
        3. Document: Full JSON representation
        4. Metadata: Flat dict for filtering

        Args:
            memory_log_id: Database ID of memory log
            embedding: Vector embedding (768D float array)
            memory_data: Complete memory log data
            user_id: User identifier for collection isolation
            project_id: Project identifier for collection isolation

        Returns:
            Memory ID string
        """
        return await memory.add_memory(
            self.client,
            memory_log_id,
            embedding,
            memory_data,
            user_id,
            project_id
        )

    async def search(
        self,
        query_embedding: List[float],
        user_id: str,
        project_id: str,
        limit: int = 10,
        where_filter: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        Perform semantic similarity search.

        Args:
            query_embedding: Query vector (768D)
            user_id: User identifier
            project_id: Project identifier
            limit: Maximum number of results
            where_filter: Optional metadata filter (ChromaDB where syntax)

        Returns:
            List of SearchResult objects sorted by similarity

        Example filter:
            {
                "component": "ui-permission-system",
                "date": {"$gte": "2025-11-01"}
            }
        """
        return await search_operations.search(
            self.client,
            query_embedding,
            user_id,
            project_id,
            limit,
            where_filter
        )

    async def get_by_id(
        self,
        memory_id: str,
        user_id: str,
        project_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve memory by ID.

        Args:
            memory_id: Memory identifier
            user_id: User identifier
            project_id: Project identifier

        Returns:
            Memory document dict or None if not found
        """
        return await memory.get_by_id(
            self.client,
            memory_id,
            user_id,
            project_id
        )

    async def delete(
        self,
        memory_id: str,
        user_id: str,
        project_id: str
    ) -> bool:
        """
        Delete memory from collection.

        Args:
            memory_id: Memory identifier
            user_id: User identifier
            project_id: Project identifier

        Returns:
            True if deleted, False if not found
        """
        return await memory.delete(
            self.client,
            memory_id,
            user_id,
            project_id
        )

    async def count(self, user_id: str, project_id: str) -> int:
        """
        Count memories in collection.

        Args:
            user_id: User identifier
            project_id: Project identifier

        Returns:
            Number of memories in collection
        """
        return await memory.count(
            self.client,
            user_id,
            project_id
        )
