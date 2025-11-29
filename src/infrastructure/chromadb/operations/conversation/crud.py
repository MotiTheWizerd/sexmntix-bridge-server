"""
Conversation CRUD Operations.

Core database operations for conversation storage in:
1. ChromaDB (separate collection for vector search)
2. File System (JSON files in data/users/user_{user_id}/conversations/)
"""

import json
from typing import Dict, Any, Optional, List

from src.infrastructure.chromadb.client import ChromaDBClient
from src.infrastructure.chromadb.utils import prepare_conversation_metadata



def generate_conversation_id(conversation_db_id: int, user_id: str) -> str:
    """
    Generate unique conversation ID for ChromaDB.

    Format: conversation_{db_id}_{user_id}
    Storage structure: user_id/conversations/{conversation_id}/

    Args:
        conversation_db_id: PostgreSQL conversation ID
        user_id: User identifier

    Returns:
        Unique conversation ID string
    """
    return f"conversation_{conversation_db_id}_{user_id}"


def build_conversation_document(conversation_data: Dict[str, Any]) -> str:
    """
    Build JSON document string from conversation data.

    Args:
        conversation_data: Complete conversation data

    Returns:
        JSON string representation
    """
    return json.dumps(conversation_data, ensure_ascii=False)


async def create_conversation(
    client: ChromaDBClient,
    conversation_db_id: int,
    embedding: List[float],
    conversation_data: Dict[str, Any],
    user_id: str,
    project_id: str,
    memory_index: Optional[int] = None,
    session_id: Optional[str] = None
) -> str:
    """
    Create and store a conversation memory unit in ChromaDB.

    Storage layers:
    1. ChromaDB: Vector embeddings for semantic search (conversations_{hash} collection)
    2. File System: JSON file at data/users/user_{user_id}/conversations/conversation_{conversation_id}.json

    Args:
        client: ChromaDB client instance
        conversation_db_id: Database ID of conversation
        embedding: Vector embedding (768D float array)
        conversation_data: Gemini memory unit data (not full conversation)
        user_id: User identifier for collection isolation
        memory_index: Index of memory unit within conversation (for unique ID)
        session_id: Optional session identifier for grouping conversations

    Returns:
        Conversation ID string
    """
    # Get conversation-specific collection (separate from memory_logs/mental_notes)
    collection = client.get_conversation_collection(user_id, project_id)

    # Generate unique ID for memory unit
    if memory_index is not None:
        # Multiple memory units per conversation
        conversation_id = f"conversation_{conversation_db_id}_{user_id}_mem{memory_index}"
    else:
        # Fallback (shouldn't happen with new architecture)
        conversation_id = generate_conversation_id(conversation_db_id, user_id)

    # Prepare metadata based on data type
    if memory_index is not None:
        # Memory unit metadata (from Gemini)
        metadata = {
            "user_id": str(user_id),
            "conversation_db_id": str(conversation_db_id),
            "memory_index": memory_index,
            "document_type": "memory_unit"
        }

        # Add session_id if provided
        if session_id:
            metadata["session_id"] = str(session_id)

        # Add memory unit fields if present
        if "memory_id" in conversation_data:
            metadata["memory_id"] = str(conversation_data["memory_id"])
        if "topic" in conversation_data:
            metadata["topic"] = str(conversation_data["topic"])[:200]  # Limit length
        if "group_id" in conversation_data:
            metadata["group_id"] = str(conversation_data["group_id"])
        if "tags" in conversation_data and isinstance(conversation_data["tags"], list):
            # Store first 5 tags as comma-separated string
            metadata["tags"] = ",".join(conversation_data["tags"][:5])
    else:
        # Full conversation metadata (fallback)
        metadata = prepare_conversation_metadata(conversation_data)
        # Add session_id to fallback metadata too
        if session_id:
            metadata["session_id"] = str(session_id)

    # Build document from conversation data
    document = build_conversation_document(conversation_data)

    # Add to ChromaDB for vector search
    collection.add(
        ids=[conversation_id],
        embeddings=[embedding],
        documents=[document],
        metadatas=[metadata]
    )

    # Force HNSW index rebuild for immediate searchability
    new_count = collection.count()

    print(f"[CONVERSATION_CRUD] Added memory unit {conversation_id} to ChromaDB collection. Total count: {new_count}")

    # Note: File storage is handled at conversation level, not per memory unit
    # Memory units are stored in ChromaDB only for semantic search

    return conversation_id


async def read_conversation(
    client: ChromaDBClient,
    conversation_id: str,
    user_id: str,
    project_id: str
) -> Optional[Dict[str, Any]]:
    """
    Retrieve a conversation by ID.

    Args:
        client: ChromaDB client instance
        conversation_id: Conversation identifier
        user_id: User identifier

    Returns:
        Conversation document dict or None if not found
    """
    collection = client.get_conversation_collection(user_id, project_id)

    result = collection.get(ids=[conversation_id])

    if result["documents"] and len(result["documents"]) > 0:
        print(f"[CONVERSATION_CRUD] Retrieved conversation {conversation_id}")
        return json.loads(result["documents"][0])

    print(f"[CONVERSATION_CRUD] Conversation {conversation_id} not found")
    return None


async def delete_conversation(
    client: ChromaDBClient,
    conversation_id: str,
    user_id: str,
    project_id: str,
    actual_conversation_id: Optional[str] = None
) -> bool:
    """
    Delete a conversation from ChromaDB and file system.

    Args:
        client: ChromaDB client instance
        conversation_id: ChromaDB conversation identifier (conversation_{db_id}_{user_id})
        user_id: User identifier
        actual_conversation_id: UUID conversation ID for file system (optional)

    Returns:
        True if deleted from ChromaDB, False if not found or error occurred
    """
    collection = client.get_conversation_collection(user_id, project_id)

    try:
        # Delete from ChromaDB
        collection.delete(ids=[conversation_id])
        print(f"[CONVERSATION_CRUD] Deleted conversation {conversation_id} from ChromaDB")



        return True
    except Exception as e:
        print(f"[CONVERSATION_CRUD] Failed to delete conversation {conversation_id}: {e}")
        return False


async def count_conversations(
    client: ChromaDBClient,
    user_id: str,
    project_id: str
) -> int:
    """
    Count the number of conversations in the collection.

    Args:
        client: ChromaDB client instance
        user_id: User identifier

    Returns:
        Number of conversations in collection
    """
    collection = client.get_conversation_collection(user_id, project_id)
    return collection.count()


async def search_conversations(
    client: ChromaDBClient,
    query_embedding: List[float],
    user_id: str,
    project_id: str,
    limit: int = 10,
    where_filter: Optional[Dict[str, Any]] = None,
    min_similarity: Optional[float] = None
) -> List[Dict[str, Any]]:
    """
    Search conversations using semantic similarity.

    Args:
        client: ChromaDB client instance
        query_embedding: Query vector (768D)
        user_id: User identifier
        limit: Maximum number of results
        where_filter: Optional metadata filter (ChromaDB where syntax)
        min_similarity: Optional minimum similarity threshold (0.0 to 1.0)

    Returns:
        List of search results with id, document, metadata, distance, and similarity
    """
    from src.infrastructure.chromadb.utils import sanitize_filter

    # Get conversation collection (user+project scoped)
    collection = client.get_conversation_collection(user_id, project_id)
    collection_count = collection.count()

    print(f"[CONVERSATION_SEARCH] Searching user_id={user_id}, collection={collection.name}, count={collection_count}, limit={limit}")

    # Sanitize filter
    where_filter = sanitize_filter(where_filter)

    # Query ChromaDB
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=limit,
        where=where_filter,
        include=["documents", "metadatas", "distances"]
    )

    results_count = len(results.get('ids', [[]])[0]) if results.get('ids') else 0
    print(f"[CONVERSATION_SEARCH] ChromaDB returned {results_count} results")

    # Convert to search result dicts
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
            
            # Log similarity scores for debugging
            print(f"[CONVERSATION_SEARCH] Result {i}: distance={distance:.4f}, similarity={similarity:.4f}, min_threshold={min_similarity}")

            # Apply minimum similarity filter if provided
            if min_similarity is not None and similarity < min_similarity:
                print(f"[CONVERSATION_SEARCH] Filtered out result {i} (similarity {similarity:.4f} < {min_similarity})")
                continue

            search_results.append({
                "id": ids[i],
                "document": document_dict,
                "metadata": metadata_dict,
                "distance": distance,
                "similarity": similarity
            })

    print(f"[CONVERSATION_SEARCH] Returning {len(search_results)} results after filtering")
    return search_results
