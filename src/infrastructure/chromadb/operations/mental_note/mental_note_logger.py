"""Mental Note Logger - Logging utilities for mental note operations"""

from typing import Dict, Any
from src.modules.core.telemetry.logger import get_logger


logger = get_logger(__name__)


def log_mental_note_addition(
    mental_note_id: str,
    user_id: str,
    project_id: str,
    mental_note_data: Dict[str, Any],
    collection_count: int
) -> None:
    """Log mental note addition to collection.

    Args:
        mental_note_id: The generated mental note ID
        user_id: User identifier
        project_id: Project identifier
        mental_note_data: Mental note data being added
        collection_count: Count of mental notes in collection after addition
    """
    content_preview = mental_note_data.get("content", "")[:100]
    session_id = mental_note_data.get("sessionId", mental_note_data.get("session_id", ""))

    logger.info(
        f"[MENTAL_NOTE_REPO] add_mental_note - mental_note_id={mental_note_id}, "
        f"session_id={session_id}, user_id={user_id}, project_id={project_id}"
    )
    logger.info(
        f"[MENTAL_NOTE_REPO] add_mental_note - mental_note_data keys: {list(mental_note_data.keys())}"
    )
    logger.info(
        f"[MENTAL_NOTE_REPO] add_mental_note - content exists: {bool(mental_note_data.get('content'))}, "
        f"length: {len(mental_note_data.get('content', ''))}, preview: {content_preview}"
    )
    logger.info(
        f"[MENTAL_NOTE_REPO] add_mental_note - Successfully stored mental note. Collection count: {collection_count}"
    )


def log_mental_note_retrieval(mental_note_id: str, found: bool) -> None:
    """Log mental note retrieval attempt.

    Args:
        mental_note_id: The mental note ID being retrieved
        found: Whether the mental note was found
    """
    status = "found" if found else "not found"
    logger.info(f"[MENTAL_NOTE_REPO] get_mental_note - mental_note_id={mental_note_id}, status={status}")


def log_mental_note_deletion(mental_note_id: str, success: bool) -> None:
    """Log mental note deletion attempt.

    Args:
        mental_note_id: The mental note ID being deleted
        success: Whether the deletion was successful
    """
    status = "deleted" if success else "failed"
    logger.info(f"[MENTAL_NOTE_REPO] delete_mental_note - mental_note_id={mental_note_id}, status={status}")
