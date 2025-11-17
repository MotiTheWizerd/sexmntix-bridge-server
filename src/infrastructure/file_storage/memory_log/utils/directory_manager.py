"""
Directory Manager Utilities for Memory Log Storage

Handles directory creation and management with error handling and logging.
"""

from pathlib import Path
from src.modules.core.telemetry.logger import get_logger

logger = get_logger(__name__)


def ensure_directory_exists(directory_path: Path, log_prefix: str = "DIRECTORY_MANAGER") -> bool:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        directory_path: Path to directory
        log_prefix: Prefix for log messages (for context)

    Returns:
        True if directory exists or was created successfully, False on error
    """
    try:
        directory_path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"[{log_prefix}] Ensured directory exists: {directory_path}")
        return True
    except Exception as e:
        logger.error(f"[{log_prefix}] Failed to create directory {directory_path}: {e}")
        return False


def directory_exists(directory_path: Path) -> bool:
    """
    Check if a directory exists.

    Args:
        directory_path: Path to directory

    Returns:
        True if directory exists and is a directory, False otherwise
    """
    return directory_path.exists() and directory_path.is_dir()


def create_directory_structure(
    base_path: Path,
    subdirectories: list[str],
    log_prefix: str = "DIRECTORY_MANAGER"
) -> bool:
    """
    Create a nested directory structure.

    Args:
        base_path: Base directory path
        subdirectories: List of subdirectory names to create under base_path
        log_prefix: Prefix for log messages

    Returns:
        True if all directories created successfully, False on any error
    """
    try:
        for subdir in subdirectories:
            dir_path = base_path / subdir
            if not ensure_directory_exists(dir_path, log_prefix):
                return False
        return True
    except Exception as e:
        logger.error(f"[{log_prefix}] Failed to create directory structure: {e}")
        return False
