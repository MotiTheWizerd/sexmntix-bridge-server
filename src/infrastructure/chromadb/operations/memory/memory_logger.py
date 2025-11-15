"""Memory Logger - Logging utilities for memory operations"""

from typing import Dict, Any
from src.modules.core.telemetry.logger import get_logger


logger = get_logger(__name__)


def log_memory_addition(
    memory_id: str,
    user_id: str,
    project_id: str,
    memory_data: Dict[str, Any],
    collection_count: int
) -> None:
    """Log memory addition to collection.

    Args:
        memory_id: The generated memory ID
        user_id: User identifier
        project_id: Project identifier
        memory_data: Memory data being added
        collection_count: Count of memories in collection after addition
    """
    content_preview = memory_data.get("content", "")[:100]

    logger.info(
        f"[VECTOR_REPO] add_memory - memory_id={memory_id}, user_id={user_id}, project_id={project_id}"
    )
    logger.info(
        f"[VECTOR_REPO] add_memory - memory_data keys: {list(memory_data.keys())}"
    )
    logger.info(
        f"[VECTOR_REPO] add_memory - content exists: {bool(memory_data.get('content'))}, "
        f"length: {len(memory_data.get('content', ''))}, preview: {content_preview}"
    )
    logger.debug(
        f"[VECTOR_REPO] add_memory - document_summary keys: {list(memory_data.keys())}"
    )
    logger.info(
        f"[VECTOR_REPO] add_memory - Successfully stored memory. Collection count: {collection_count}"
    )


def log_memory_retrieval(memory_id: str, found: bool) -> None:
    """Log memory retrieval attempt.

    Args:
        memory_id: The memory ID being retrieved
        found: Whether the memory was found
    """
    status = "found" if found else "not found"
    logger.info(f"[VECTOR_REPO] get_memory - memory_id={memory_id}, status={status}")


def log_memory_deletion(memory_id: str, success: bool) -> None:
    """Log memory deletion attempt.

    Args:
        memory_id: The memory ID being deleted
        success: Whether the deletion was successful
    """
    status = "deleted" if success else "failed"
    logger.info(f"[VECTOR_REPO] delete_memory - memory_id={memory_id}, status={status}")
