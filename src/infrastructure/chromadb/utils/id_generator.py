"""Memory ID Generator

Generates unique memory identifiers for ChromaDB storage.
"""


def generate_memory_id(memory_log_id: int, user_id: str, project_id: str) -> str:
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
