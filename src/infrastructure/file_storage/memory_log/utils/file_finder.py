"""
File Finder Utilities for Memory Log Storage

Handles file listing, existence checks, and pattern matching.
"""

from pathlib import Path
from typing import List
from src.modules.core.telemetry.logger import get_logger

logger = get_logger(__name__)


def list_files_by_pattern(
    directory: Path,
    pattern: str,
    log_prefix: str = "FILE_FINDER"
) -> List[Path]:
    """
    List all files in a directory matching a glob pattern.

    Args:
        directory: Directory to search in
        pattern: Glob pattern to match (e.g., "memory_*.json")
        log_prefix: Prefix for log messages

    Returns:
        List of Path objects matching the pattern, empty list if directory doesn't exist
    """
    if not directory.exists():
        logger.debug(f"[{log_prefix}] Directory does not exist: {directory}")
        return []

    try:
        files = list(directory.glob(pattern))
        logger.debug(f"[{log_prefix}] Found {len(files)} files matching pattern '{pattern}' in {directory}")
        return files
    except Exception as e:
        logger.error(f"[{log_prefix}] Failed to list files in {directory}: {e}")
        return []


def file_exists(file_path: Path) -> bool:
    """
    Check if a file exists.

    Args:
        file_path: Path to file

    Returns:
        True if file exists and is a file, False otherwise
    """
    return file_path.exists() and file_path.is_file()


def count_files_by_pattern(directory: Path, pattern: str) -> int:
    """
    Count files in a directory matching a glob pattern.

    Args:
        directory: Directory to search in
        pattern: Glob pattern to match

    Returns:
        Number of files matching the pattern
    """
    return len(list_files_by_pattern(directory, pattern))


def get_file_size(file_path: Path) -> int:
    """
    Get size of a file in bytes.

    Args:
        file_path: Path to file

    Returns:
        File size in bytes, or 0 if file doesn't exist
    """
    try:
        if file_exists(file_path):
            return file_path.stat().st_size
        return 0
    except Exception:
        return 0


def find_latest_file(directory: Path, pattern: str) -> Path | None:
    """
    Find the most recently modified file matching a pattern.

    Args:
        directory: Directory to search in
        pattern: Glob pattern to match

    Returns:
        Path to most recent file, or None if no files found
    """
    files = list_files_by_pattern(directory, pattern)
    if not files:
        return None

    try:
        return max(files, key=lambda p: p.stat().st_mtime)
    except Exception as e:
        logger.error(f"[FILE_FINDER] Failed to find latest file: {e}")
        return None
