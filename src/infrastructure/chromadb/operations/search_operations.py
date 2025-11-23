"""Search Operations

Semantic similarity search operations.
"""

import json
from typing import Dict, Any, Optional, List

from src.infrastructure.chromadb.client import ChromaDBClient
from src.infrastructure.chromadb.models import SearchResult
from src.modules.core.telemetry.logger import get_logger
from src.infrastructure.chromadb.utils import sanitize_filter


logger = get_logger(__name__)


async def search(
    client: ChromaDBClient,
    query_embedding: List[float],
    user_id: str,
    project_id: str,
    limit: int = 10,
    where_filter: Optional[Dict[str, Any]] = None,
    collection_prefix: Optional[str] = None,
    min_similarity: Optional[float] = None
) -> List[SearchResult]:
    """
    Perform semantic similarity search.

    Args:
        client: ChromaDB client instance
        query_embedding: Query vector (768D)
        user_id: User identifier
        project_id: Project identifier
        limit: Maximum number of results
        where_filter: Optional metadata filter (ChromaDB where syntax)
        min_similarity: Optional minimum similarity threshold (0.0 to 1.0)

    Returns:
        List of SearchResult objects sorted by similarity

    Example filter:
        {
            "component": "ui-permission-system",
            "date": {"$gte": "2025-11-01"}
        }
    """
    collection = client.get_collection(
        user_id,
        project_id,
        collection_prefix=collection_prefix
    )
    collection_count = collection.count()

    logger.info(
        f"[VECTOR_REPO] search - user_id={user_id}, project_id={project_id}, "
        f"collection={collection.name}, count={collection_count}, limit={limit}"
    )

    # Sanitize filter: remove empty nested objects and convert to None if fully empty
    # ChromaDB rejects empty dicts {} as operator expressions
    where_filter = sanitize_filter(where_filter)
    logger.debug(f"[VECTOR_REPO] search - Sanitized where_filter: {where_filter}")

    # Query ChromaDB
    logger.info(
        f"[VECTOR_REPO] search - Querying with limit={limit}, embedding_dims={len(query_embedding)}"
    )
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=limit,
        where=where_filter,
        include=["documents", "metadatas", "distances"]
    )

    results_count = len(results.get('ids', [[]])[0]) if results.get('ids') else 0
    logger.info(
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

            # Calculate similarity score (1 - normalized distance)
            # ChromaDB uses L2 distance, normalize to [0, 1] range
            similarity = 1.0 - (distance / 2.0) if distance <= 2.0 else 0.0

            # Apply minimum similarity filter if provided
            if min_similarity is not None and similarity < min_similarity:
                logger.debug(
                    f"[VECTOR_REPO] search - Filtered out result {i} "
                    f"(similarity {similarity:.4f} < {min_similarity})"
                )
                continue

            search_results.append(
                SearchResult(
                    id=ids[i],
                    document=document_dict,
                    metadata=metadata_dict,
                    distance=distance
                )
            )

    return search_results
