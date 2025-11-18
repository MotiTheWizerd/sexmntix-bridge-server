"""
File Finder for Mental Note Storage

Handles file discovery and existence checks.
"""

from pathlib import Path
from typing import List
from src.modules.core.telemetry.logger import get_logger

logger = get_logger(__name__)


def list_files_by_pattern(directory: Path, pattern: str, log_prefix: str = "MENTAL_NOTE") -> List[Path]:
    """
    List all files in directory matching pattern.

    Args:
        directory: Directory to search
        pattern: Glob pattern (e.g., "mental_note_*.json")
        log_prefix: Prefix for log messages

    Returns:
        List of Path objects for matching files
    """
    try:
        if not directory.exists():
            logger.warning(f"[{log_prefix}] Directory does not exist: {directory}")
            return []

        files = list(directory.glob(pattern))
        logger.debug(f"[{log_prefix}] Found {len(files)} files matching pattern '{pattern}' in {directory}")
        return files

    except Exception as e:
        logger.error(
            f"[{log_prefix}] Failed to list files in {directory}: {e}",
            exc_info=True
        )
        return []


def file_exists(file_path: Path) -> bool:
    """
    Check if a file exists.

    Args:
        file_path: Path to check

    Returns:
        True if file exists, False otherwise
    """
    return file_path.exists() and file_path.is_file()
