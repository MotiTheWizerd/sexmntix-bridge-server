"""
Vector Repository for ChromaDB Operations

Handles storage, retrieval, and semantic search of vector embeddings.
Based on TypeScript architecture from 03-chromadb-storage.md.

Operations:
- add_memory: Store vector with metadata
- search: Semantic similarity search
- get_by_id: Retrieve specific memory
- delete: Remove memory from collection
"""

import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from chromadb import Collection

from .client import ChromaDBClient
from src.modules.core.telemetry.logger import get_logger


class SearchResult:
    """
    Search result with similarity scoring.

    Attributes:
        id: Memory identifier
        document: Full memory JSON
        metadata: Flat metadata dict
        distance: L2 distance from query
        similarity: Similarity percentage (0-100%)
    """

    def __init__(
        self,
        id: str,
        document: Dict[str, Any],
        metadata: Dict[str, Any],
        distance: float
    ):
        self.id = id
        self.document = document
        self.metadata = metadata
        self.distance = distance
        self.similarity = self._calculate_similarity(distance)

    @staticmethod
    def _calculate_similarity(distance: float) -> float:
        """
        Convert L2 distance to similarity percentage.

        L2 distance range: 0 to ~2.0
        - 0.0 = identical vectors (100% similarity)
        - 2.0 = completely different (0% similarity)

        Formula: similarity = max(0, 1.0 - (distance / 2.0))

        Args:
            distance: L2 distance from ChromaDB

        Returns:
            Similarity score between 0.0 and 1.0
        """
        return max(0.0, 1.0 - (distance / 2.0))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "document": self.document,
            "metadata": self.metadata,
            "distance": self.distance,
            "similarity": self.similarity
        }


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

    def _generate_memory_id(self, memory_log_id: int, user_id: str, project_id: str) -> str:
        """
        Generate unique memory identifier.

        Format: memory_{memory_log_id}_{user_id}_{project_id}

        Args:
            memory_log_id: Database ID of memory log
            user_id: User identifier
            project_id: Project identifier

        Returns:
            Unique memory ID string
        """
        return f"memory_{memory_log_id}_{user_id}_{project_id}"

    @staticmethod
    def _convert_to_timestamp(value: Any) -> Optional[int]:
        """
        Convert date value to Unix timestamp for ChromaDB storage.

        ChromaDB comparison operators ($gte, $lte) require numeric values.

        Args:
            value: Date value (datetime object, ISO string, or timestamp)

        Returns:
            Unix timestamp (seconds since epoch) or None if invalid

        Examples:
            datetime(2025, 10, 14) -> 1728864000
            "2025-10-14T00:00:00" -> 1728864000
            "2025-10-14" -> 1728864000
            1728864000 -> 1728864000
        """
        if value is None or value == "":
            return None

        # Already a timestamp (int or float)
        if isinstance(value, (int, float)):
            return int(value)

        # datetime object
        if isinstance(value, datetime):
            return int(value.timestamp())

        # String (ISO format)
        if isinstance(value, str):
            try:
                # Parse ISO string to datetime
                if "T" not in value:
                    value = f"{value}T00:00:00"
                dt = datetime.fromisoformat(value)
                return int(dt.timestamp())
            except (ValueError, AttributeError):
                return None

        return None

    def _prepare_metadata(self, memory_log: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare flat metadata dictionary for ChromaDB filtering.

        ChromaDB requires flat key-value pairs (no nested objects).
        Converts lists to comma-separated strings.

        Args:
            memory_log: Memory log data dictionary

        Returns:
            Flat metadata dictionary
        """
        metadata = {
            "task": memory_log.get("task", ""),
            "agent": memory_log.get("agent", ""),
            "component": memory_log.get("component", ""),
            "date": self._convert_to_timestamp(memory_log.get("date")),
        }

        # Handle tags (list -> comma-separated string + individual fields)
        if "tags" in memory_log and isinstance(memory_log["tags"], list):
            tags_list = memory_log["tags"]
            metadata["tags"] = ",".join(tags_list)  # Keep combined for display

            # Store first 5 tags individually for filtering
            for i, tag in enumerate(tags_list[:5]):
                metadata[f"tag_{i}"] = tag

        # Handle temporal context
        if "temporal_context" in memory_log:
            temporal = memory_log["temporal_context"]
            if isinstance(temporal, dict):
                metadata["time_period"] = temporal.get("time_period", "")
                metadata["quarter"] = temporal.get("quarter", "")
                metadata["year"] = str(temporal.get("year", ""))

        return metadata

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
        collection = self.client.get_collection(user_id, project_id)

        # Generate unique ID
        memory_id = self._generate_memory_id(memory_log_id, user_id, project_id)

        # Prepare metadata for filtering
        metadata = self._prepare_metadata(memory_data)

        # Extract essential fields for document storage including gotchas
        document_summary = {
            "content": memory_data.get("content", ""),  # Main content from store_memory
            "task": memory_data.get("task", ""),
            "summary": memory_data.get("summary", ""),
            "component": memory_data.get("component", ""),
            "tags": memory_data.get("tags", [])[:10],  # Limit tags
            "gotchas": memory_data.get("gotchas", []),  # Important: issue/solution pairs
            "lesson": memory_data.get("lesson", ""),
            "root_cause": memory_data.get("root_cause", ""),
            "solution": memory_data.get("solution", {}),  # Full solution object
            "files_touched": memory_data.get("files_touched", []),  # Files modified
        }

        content_preview = document_summary.get('content', '')[:100]
        self.logger.info(
            f"[VECTOR_REPO] add_memory - memory_id={memory_id}, user_id={user_id}, project_id={project_id}"
        )
        self.logger.info(
            f"[VECTOR_REPO] add_memory - memory_data keys: {list(memory_data.keys())}"
        )
        self.logger.info(
            f"[VECTOR_REPO] add_memory - content exists: {bool(document_summary.get('content'))}, "
            f"length: {len(document_summary.get('content', ''))}, preview: {content_preview}"
        )
        self.logger.debug(
            f"[VECTOR_REPO] add_memory - document_summary keys: {list(document_summary.keys())}"
        )

        # Convert document to JSON string
        document = json.dumps(document_summary, default=str)

        # Add to ChromaDB
        collection.add(
            ids=[memory_id],
            embeddings=[embedding],
            documents=[document],
            metadatas=[metadata]
        )

        # Force HNSW index rebuild for immediate searchability
        # See: chromadb-hnsw-index-immediate-persistence-fix
        new_count = collection.count()

        self.logger.info(
            f"[VECTOR_REPO] add_memory - Successfully stored memory. Collection count: {new_count}"
        )

        return memory_id

    def _build_tag_filter(self, tag: str) -> Dict[str, Any]:
        """
        Build a filter to match any of the individual tag fields.

        Args:
            tag: Tag value to search for

        Returns:
            ChromaDB $or filter matching tag_0 through tag_4

        Example:
            Input: "chromadb"
            Output: {"$or": [{"tag_0": "chromadb"}, {"tag_1": "chromadb"}, ...]}
        """
        return {
            "$or": [
                {"tag_0": tag},
                {"tag_1": tag},
                {"tag_2": tag},
                {"tag_3": tag},
                {"tag_4": tag}
            ]
        }

    def _sanitize_filter(self, where_filter: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Sanitize ChromaDB where filter by removing empty nested objects and transforming date filters.

        ChromaDB requires each filter key to have a valid operator expression.
        Empty dicts {} are not valid and cause "Expected operator expression" errors.

        Also handles date range filtering (dates are converted to Unix timestamps):
        - 'date' field -> {'date': {'$gte': timestamp}}
        - 'end_date' field -> {'date': {'$lte': timestamp}}
        - Both combined with $and

        Args:
            where_filter: Optional metadata filter

        Returns:
            Sanitized filter or None if empty after cleaning

        Example:
            Input:  {"additionalProp1": {}, "component": "auth"}
            Output: {"component": "auth"}

            Input:  {"date": "2025-10-14", "end_date": "2025-11-13"}
            Output: {"$and": [{"date": {"$gte": 1728864000}}, {"date": {"$lte": 1731542399}}]}

            Input:  {"additionalProp1": {}}
            Output: None
        """
        if where_filter is None:
            return None

        # Remove keys with empty dict values
        cleaned_filter = {
            key: value
            for key, value in where_filter.items()
            if not (isinstance(value, dict) and len(value) == 0)
        }

        # Handle date range filtering
        date_filters = []
        other_filters = {}

        for key, value in cleaned_filter.items():
            if key == "date":
                if isinstance(value, dict):
                    # Date already has operators like {"$gte": "2025-10-14", "$lte": "2025-11-13"}
                    # Convert all operator values to timestamps
                    converted_ops = {}
                    for op, date_val in value.items():
                        timestamp = self._convert_to_timestamp(date_val)
                        if timestamp is not None:
                            converted_ops[op] = timestamp
                    if converted_ops:
                        other_filters["date"] = converted_ops
                else:
                    # Transform plain date value to $gte operator with timestamp conversion
                    timestamp = self._convert_to_timestamp(value)
                    if timestamp is not None:
                        date_filters.append({"date": {"$gte": timestamp}})
            elif key == "end_date":
                # Transform end_date to $lte operator on date field with timestamp conversion
                timestamp = self._convert_to_timestamp(value)
                if timestamp is not None:
                    date_filters.append({"date": {"$lte": timestamp}})
            else:
                other_filters[key] = value

        # Build final filter
        if date_filters:
            if len(date_filters) == 1:
                date_filter = date_filters[0]
            else:
                date_filter = {"$and": date_filters}

            # Combine with other filters
            if other_filters:
                return {"$and": [other_filters, date_filter]}
            else:
                return date_filter

        # Return None if filter is empty after cleaning
        if len(other_filters) == 0:
            return None

        return other_filters

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
        collection = self.client.get_collection(user_id, project_id)
        collection_count = collection.count()

        self.logger.info(
            f"[VECTOR_REPO] search - user_id={user_id}, project_id={project_id}, "
            f"collection={collection.name}, count={collection_count}, limit={limit}"
        )

        # Sanitize filter: remove empty nested objects and convert to None if fully empty
        # ChromaDB rejects empty dicts {} as operator expressions
        where_filter = self._sanitize_filter(where_filter)
        self.logger.debug(f"[VECTOR_REPO] search - Sanitized where_filter: {where_filter}")

        # Query ChromaDB
        self.logger.info(
            f"[VECTOR_REPO] search - Querying with limit={limit}, embedding_dims={len(query_embedding)}"
        )
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )

        results_count = len(results.get('ids', [[]])[0]) if results.get('ids') else 0
        self.logger.info(
            f"[VECTOR_REPO] search - ChromaDB returned {results_count} results"
        )

        # Convert to SearchResult objects
        search_results = []

        if results["ids"] and len(results["ids"]) > 0:
            ids = results["ids"][0]
            documents = results["documents"][0] if results["documents"] else []
            metadatas = results["metadatas"][0] if results["metadatas"] else []
            distances = results["distances"][0] if results["distances"] else []

            for i in range(len(ids)):
                document_dict = json.loads(documents[i]) if i < len(documents) else {}
                metadata_dict = metadatas[i] if i < len(metadatas) else {}
                distance = distances[i] if i < len(distances) else 2.0

                search_results.append(
                    SearchResult(
                        id=ids[i],
                        document=document_dict,
                        metadata=metadata_dict,
                        distance=distance
                    )
                )

        return search_results

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
        collection = self.client.get_collection(user_id, project_id)

        result = collection.get(ids=[memory_id])

        if result["documents"] and len(result["documents"]) > 0:
            return json.loads(result["documents"][0])

        return None

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
        collection = self.client.get_collection(user_id, project_id)

        try:
            collection.delete(ids=[memory_id])
            return True
        except Exception:
            return False

    async def count(self, user_id: str, project_id: str) -> int:
        """
        Count memories in collection.

        Args:
            user_id: User identifier
            project_id: Project identifier

        Returns:
            Number of memories in collection
        """
        collection = self.client.get_collection(user_id, project_id)
        return collection.count()
