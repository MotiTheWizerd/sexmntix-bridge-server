"""Memory CRUD Operations - Core database operations for memory storage and retrieval"""

import json
from typing import Dict, Any, Optional, List

from src.infrastructure.chromadb.client import ChromaDBClient
from src.infrastructure.chromadb.utils import prepare_metadata, generate_memory_id
from src.infrastructure.chromadb.operations.memory.document_builder import (
    build_memory_document,
    get_content_preview
)
from src.infrastructure.chromadb.operations.memory.memory_logger import (
    log_memory_addition,
    log_memory_retrieval,
    log_memory_deletion
)


async def create_memory(
    client: ChromaDBClient,
    memory_log_id: int,
    embedding: List[float],
    memory_data: Dict[str, Any],
    user_id: str,
    project_id: str,
    collection_prefix: str = "memory_logs"
) -> str:
    """Create and store a memory embedding in ChromaDB collection.

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
    if collection_prefix == "memory_logs":
        collection = client.get_memory_logs_collection(user_id, project_id)
    else:
        collection = client.get_collection(user_id, project_id, collection_prefix=collection_prefix)

    # Generate unique ID
    memory_id = generate_memory_id(memory_log_id, user_id, project_id)

    # Prepare metadata for filtering with document_type
    metadata = prepare_metadata(memory_data, document_type="memory_log")

    # Build document from memory data
    document = build_memory_document(memory_data)

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

    # Log the operation
    log_memory_addition(memory_id, user_id, project_id, memory_data, new_count)

    return memory_id


async def read_memory(
    client: ChromaDBClient,
    memory_id: str,
    user_id: str,
    project_id: str,
    collection_prefix: str = "memory_logs"
) -> Optional[Dict[str, Any]]:
    """Retrieve a memory by ID.

    Args:
        client: ChromaDB client instance
        memory_id: Memory identifier
        user_id: User identifier
        project_id: Project identifier

    Returns:
        Memory document dict or None if not found
    """
    if collection_prefix == "memory_logs":
        collection = client.get_memory_logs_collection(user_id, project_id)
    else:
        collection = client.get_collection(user_id, project_id, collection_prefix=collection_prefix)

    result = collection.get(ids=[memory_id])

    if result["documents"] and len(result["documents"]) > 0:
        log_memory_retrieval(memory_id, True)
        return json.loads(result["documents"][0])

    log_memory_retrieval(memory_id, False)
    return None


async def delete_memory(
    client: ChromaDBClient,
    memory_id: str,
    user_id: str,
    project_id: str,
    collection_prefix: str = "memory_logs"
) -> bool:
    """Delete a memory from the collection.

    Args:
        client: ChromaDB client instance
        memory_id: Memory identifier
        user_id: User identifier
        project_id: Project identifier

    Returns:
        True if deleted, False if not found or error occurred
    """
    if collection_prefix == "memory_logs":
        collection = client.get_memory_logs_collection(user_id, project_id)
    else:
        collection = client.get_collection(user_id, project_id, collection_prefix=collection_prefix)

    try:
        collection.delete(ids=[memory_id])
        log_memory_deletion(memory_id, True)
        return True
    except Exception:
        log_memory_deletion(memory_id, False)
        return False


async def count_memories(
    client: ChromaDBClient,
    user_id: str,
    project_id: str,
    collection_prefix: str = "memory_logs"
) -> int:
    """Count the number of memories in a collection.

    Args:
        client: ChromaDB client instance
        user_id: User identifier
        project_id: Project identifier

    Returns:
        Number of memories in collection
    """
    # collection_prefix kept for backward compatibility if callers forward dynamic values
    if collection_prefix == "memory_logs":
        collection = client.get_memory_logs_collection(user_id, project_id)
    else:
        collection = client.get_collection(user_id, project_id, collection_prefix=collection_prefix)
    return collection.count()
