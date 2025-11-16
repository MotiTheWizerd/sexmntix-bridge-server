"""Mental Note CRUD Operations - Core database operations for mental note storage and retrieval"""

import json
from typing import Dict, Any, Optional, List

from src.infrastructure.chromadb.client import ChromaDBClient
from src.infrastructure.chromadb.utils import prepare_metadata, generate_memory_id
from src.infrastructure.chromadb.operations.mental_note.document_builder import (
    build_mental_note_document,
    get_content_preview
)
from src.infrastructure.chromadb.operations.mental_note.mental_note_logger import (
    log_mental_note_addition,
    log_mental_note_retrieval,
    log_mental_note_deletion
)


async def create_mental_note(
    client: ChromaDBClient,
    mental_note_id: int,
    embedding: List[float],
    mental_note_data: Dict[str, Any],
    user_id: str,
    project_id: str
) -> str:
    """Create and store a mental note embedding in ChromaDB collection.

    Stores 4 components:
    1. ID: Unique identifier
    2. Embedding: 768-dimensional vector
    3. Document: Full JSON representation
    4. Metadata: Flat dict for filtering

    Args:
        client: ChromaDB client instance
        mental_note_id: Database ID of mental note
        embedding: Vector embedding (768D float array)
        mental_note_data: Complete mental note data
        user_id: User identifier for collection isolation
        project_id: Project identifier for collection isolation

    Returns:
        Mental note ID string
    """
    collection = client.get_collection(user_id, project_id)

    # Generate unique ID using same pattern as memory logs
    note_id = generate_memory_id(mental_note_id, user_id, project_id)

    # Prepare metadata for filtering with document_type
    metadata = prepare_metadata(mental_note_data, document_type="mental_note")

    # Build document from mental note data
    document = build_mental_note_document(mental_note_data)

    # Add to ChromaDB
    collection.add(
        ids=[note_id],
        embeddings=[embedding],
        documents=[document],
        metadatas=[metadata]
    )

    # Force HNSW index rebuild for immediate searchability
    new_count = collection.count()

    # Log the operation
    log_mental_note_addition(note_id, user_id, project_id, mental_note_data, new_count)

    return note_id


async def read_mental_note(
    client: ChromaDBClient,
    mental_note_id: str,
    user_id: str,
    project_id: str
) -> Optional[Dict[str, Any]]:
    """Retrieve a mental note by ID.

    Args:
        client: ChromaDB client instance
        mental_note_id: Mental note identifier
        user_id: User identifier
        project_id: Project identifier

    Returns:
        Mental note document dict or None if not found
    """
    collection = client.get_collection(user_id, project_id)

    result = collection.get(ids=[mental_note_id])

    if result["documents"] and len(result["documents"]) > 0:
        log_mental_note_retrieval(mental_note_id, True)
        return json.loads(result["documents"][0])

    log_mental_note_retrieval(mental_note_id, False)
    return None


async def delete_mental_note(
    client: ChromaDBClient,
    mental_note_id: str,
    user_id: str,
    project_id: str
) -> bool:
    """Delete a mental note from the collection.

    Args:
        client: ChromaDB client instance
        mental_note_id: Mental note identifier
        user_id: User identifier
        project_id: Project identifier

    Returns:
        True if deleted, False if not found or error occurred
    """
    collection = client.get_collection(user_id, project_id)

    try:
        collection.delete(ids=[mental_note_id])
        log_mental_note_deletion(mental_note_id, True)
        return True
    except Exception:
        log_mental_note_deletion(mental_note_id, False)
        return False


async def count_mental_notes(
    client: ChromaDBClient,
    user_id: str,
    project_id: str
) -> int:
    """Count the number of mental notes in a collection.

    Args:
        client: ChromaDB client instance
        user_id: User identifier
        project_id: Project identifier

    Returns:
        Number of mental notes in collection
    """
    collection = client.get_collection(user_id, project_id)
    return collection.count()
