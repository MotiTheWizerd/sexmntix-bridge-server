"""
ID Parser Utilities for Memory Log Storage

Handles extraction of IDs from filenames and validation.
Pure functions with no I/O operations.
"""

from pathlib import Path
from typing import Optional
from src.modules.core.telemetry.logger import get_logger

logger = get_logger(__name__)


def extract_id_from_filename(
    file_path: Path,
    prefix: str,
    suffix: str = ".json",
    log_prefix: str = "ID_PARSER"
) -> Optional[int]:
    """
    Extract numeric ID from filename with given prefix and suffix.

    Generic utility that works with any prefix pattern.

    Args:
        file_path: Path to file
        prefix: Expected prefix (e.g., "memory_")
        suffix: Expected suffix (e.g., ".json")
        log_prefix: Prefix for log messages

    Returns:
        Extracted integer ID or None if invalid format

    Examples:
        extract_id_from_filename(Path("memory_42.json"), "memory_") → 42
        extract_id_from_filename(Path("conversation_99.json"), "conversation_") → 99
    """
    filename = file_path.stem  # Gets filename without extension

    if not filename.startswith(prefix):
        logger.debug(f"[{log_prefix}] Filename does not start with prefix '{prefix}': {filename}")
        return None

    # Extract the ID part
    id_string = filename[len(prefix):]

    try:
        return int(id_string)
    except ValueError:
        logger.warning(f"[{log_prefix}] Invalid ID in filename: {filename} (expected integer after '{prefix}')")
        return None


def extract_memory_log_id(file_path: Path) -> Optional[int]:
    """
    Extract memory log ID from filename.

    Convenience wrapper for memory log files.

    Args:
        file_path: Path to memory log file

    Returns:
        Memory log ID or None if invalid filename
    """
    return extract_id_from_filename(file_path, "memory_", ".json", "MEMORY_ID_PARSER")


def validate_id_format(id_value: any, min_value: int = 1) -> bool:
    """
    Validate that an ID is a valid positive integer.

    Args:
        id_value: Value to validate
        min_value: Minimum acceptable value (default: 1)

    Returns:
        True if valid, False otherwise
    """
    try:
        int_value = int(id_value)
        return int_value >= min_value
    except (ValueError, TypeError):
        return False


def parse_id_list(file_paths: list[Path], prefix: str = "memory_") -> list[int]:
    """
    Extract all valid IDs from a list of file paths.

    Args:
        file_paths: List of file paths
        prefix: Prefix to look for in filenames

    Returns:
        Sorted list of valid integer IDs
    """
    ids = []
    for file_path in file_paths:
        id_value = extract_id_from_filename(file_path, prefix)
        if id_value is not None:
            ids.append(id_value)

    return sorted(ids)
