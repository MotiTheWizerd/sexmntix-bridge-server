"""
Directory Manager for Mental Note Storage

Handles directory creation with error handling and logging.
"""

from pathlib import Path
from src.modules.core.telemetry.logger import get_logger

logger = get_logger(__name__)


def ensure_directory_exists(directory: Path, log_prefix: str = "MENTAL_NOTE") -> bool:
    """
    Ensure directory exists, creating it if necessary.

    Args:
        directory: Directory path to check/create
        log_prefix: Prefix for log messages

    Returns:
        True if directory exists or was created, False on error
    """
    try:
        directory.mkdir(parents=True, exist_ok=True)
        logger.debug(f"[{log_prefix}] Directory exists or created: {directory}")
        return True

    except Exception as e:
        logger.error(
            f"[{log_prefix}] Failed to create directory {directory}: {e}",
            exc_info=True
        )
        return False
