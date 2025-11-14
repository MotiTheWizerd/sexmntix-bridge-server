"""
Collection Naming Strategy

Provides hash-based collection naming to meet ChromaDB's 3-63 character limit.
"""

import hashlib
from .config import ChromaDBConfig, DEFAULT_CONFIG


def create_collection_name(
    user_id: str,
    project_id: str,
    prefix: str = "semantix",
    config: ChromaDBConfig = DEFAULT_CONFIG
) -> str:
    """
    Create a collection name that meets ChromaDB requirements.

    ChromaDB requires collection names to be 3-63 characters.
    Since UUIDs are long, we use a hash-based approach:
    - prefix_hash16
    - hash16 is first 16 chars of SHA256(user_id:project_id)

    Example:
    - Input: user_id=9b1cdb78-df73-4ae4-8f80-41be3c0fdc1e, project_id=1c712e4d-13bf-43da-a01c-91001b9014f1
    - Output: semantix_a1b2c3d4e5f6g7h8

    Args:
        user_id: User identifier
        project_id: Project identifier
        prefix: Collection prefix (default: "semantix")
        config: ChromaDB configuration (default: DEFAULT_CONFIG)

    Returns:
        Collection name (3-63 characters)

    Raises:
        ValueError: If collection name doesn't meet ChromaDB requirements
    """
    # Create a unique hash from user_id and project_id
    combined = f"{user_id}:{project_id}"
    hash_digest = hashlib.sha256(combined.encode()).hexdigest()

    # Take first N characters of hash for uniqueness
    hash_short = hash_digest[: config.hash_length]

    # Create collection name: prefix_hash
    collection_name = f"{prefix}_{hash_short}"

    # Validate collection name meets ChromaDB requirements
    if len(collection_name) < config.min_collection_name_length:
        raise ValueError(
            f"Collection name '{collection_name}' is too short. "
            f"Minimum length: {config.min_collection_name_length}"
        )

    if len(collection_name) > config.max_collection_name_length:
        raise ValueError(
            f"Collection name '{collection_name}' is too long. "
            f"Maximum length: {config.max_collection_name_length}"
        )

    return collection_name
