"""Memory Operations

CRUD operations for memory storage and retrieval.
"""

import json
from typing import Dict, Any, Optional, List

from src.infrastructure.chromadb.client import ChromaDBClient
from src.modules.core.telemetry.logger import get_logger
from src.infrastructure.chromadb.utils import prepare_metadata, generate_memory_id


logger = get_logger(__name__)


async def add_memory(
    client: ChromaDBClient,
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
        client: ChromaDB client instance
        memory_log_id: Database ID of memory log
        embedding: Vector embedding (768D float array)
        memory_data: Complete memory log data
        user_id: User identifier for collection isolation
        project_id: Project identifier for collection isolation

    Returns:
        Memory ID string
    """
    collection = client.get_collection(user_id, project_id)

    # Generate unique ID
    memory_id = generate_memory_id(memory_log_id, user_id, project_id)

    # Prepare metadata for filtering
    metadata = prepare_metadata(memory_data)

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
    }

    content_preview = document_summary.get('content', '')[:100]
    logger.info(
        f"[VECTOR_REPO] add_memory - memory_id={memory_id}, user_id={user_id}, project_id={project_id}"
    )
    logger.info(
        f"[VECTOR_REPO] add_memory - memory_data keys: {list(memory_data.keys())}"
    )
    logger.info(
        f"[VECTOR_REPO] add_memory - content exists: {bool(document_summary.get('content'))}, "
        f"length: {len(document_summary.get('content', ''))}, preview: {content_preview}"
    )
    logger.debug(
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

    logger.info(
        f"[VECTOR_REPO] add_memory - Successfully stored memory. Collection count: {new_count}"
    )

    return memory_id


async def get_by_id(
    client: ChromaDBClient,
    memory_id: str,
    user_id: str,
    project_id: str
) -> Optional[Dict[str, Any]]:
    """
    Retrieve memory by ID.

    Args:
        client: ChromaDB client instance
        memory_id: Memory identifier
        user_id: User identifier
        project_id: Project identifier

    Returns:
        Memory document dict or None if not found
    """
    collection = client.get_collection(user_id, project_id)

    result = collection.get(ids=[memory_id])

    if result["documents"] and len(result["documents"]) > 0:
        return json.loads(result["documents"][0])

    return None


async def delete(
    client: ChromaDBClient,
    memory_id: str,
    user_id: str,
    project_id: str
) -> bool:
    """
    Delete memory from collection.

    Args:
        client: ChromaDB client instance
        memory_id: Memory identifier
        user_id: User identifier
        project_id: Project identifier

    Returns:
        True if deleted, False if not found
    """
    collection = client.get_collection(user_id, project_id)

    try:
        collection.delete(ids=[memory_id])
        return True
    except Exception:
        return False


async def count(
    client: ChromaDBClient,
    user_id: str,
    project_id: str
) -> int:
    """
    Count memories in collection.

    Args:
        client: ChromaDB client instance
        user_id: User identifier
        project_id: Project identifier

    Returns:
        Number of memories in collection
    """
    collection = client.get_collection(user_id, project_id)
    return collection.count()
