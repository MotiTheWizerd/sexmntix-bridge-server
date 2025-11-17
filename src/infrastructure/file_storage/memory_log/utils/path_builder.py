"""
Path Builder Utilities for Memory Log Storage

Pure path generation functions with no I/O operations.
All functions are stateless and deterministic.
"""

from pathlib import Path


# Constants for memory log file naming
MEMORY_LOG_PREFIX = "memory_"
MEMORY_LOG_SUFFIX = ".json"
MEMORY_LOGS_FOLDER = "memory_logs"
USER_PREFIX = "user_"


def build_user_directory(base_path: Path | str, user_id: str) -> Path:
    """
    Build path to user's base directory.

    Args:
        base_path: Base directory for all user data
        user_id: User identifier

    Returns:
        Path to user's directory (e.g., data/users/user_123/)
    """
    base = Path(base_path) if isinstance(base_path, str) else base_path
    return base / f"{USER_PREFIX}{user_id}"


def build_user_memory_logs_dir(base_path: Path | str, user_id: str) -> Path:
    """
    Build path to user's memory_logs directory.

    Args:
        base_path: Base directory for all user data
        user_id: User identifier

    Returns:
        Path to user's memory_logs directory (e.g., data/users/user_123/memory_logs/)
    """
    user_dir = build_user_directory(base_path, user_id)
    return user_dir / MEMORY_LOGS_FOLDER


def build_memory_log_filename(memory_log_id: int) -> str:
    """
    Build filename for a memory log.

    Args:
        memory_log_id: Memory log ID

    Returns:
        Filename string (e.g., memory_42.json)
    """
    return f"{MEMORY_LOG_PREFIX}{memory_log_id}{MEMORY_LOG_SUFFIX}"


def build_memory_log_file_path(
    base_path: Path | str,
    user_id: str,
    memory_log_id: int
) -> Path:
    """
    Build complete file path for a memory log.

    Args:
        base_path: Base directory for all user data
        user_id: User identifier
        memory_log_id: Memory log ID

    Returns:
        Complete path to memory log file (e.g., data/users/user_123/memory_logs/memory_42.json)
    """
    memory_logs_dir = build_user_memory_logs_dir(base_path, user_id)
    filename = build_memory_log_filename(memory_log_id)
    return memory_logs_dir / filename


def get_glob_pattern() -> str:
    """
    Get glob pattern for matching memory log files.

    Returns:
        Glob pattern string (e.g., memory_*.json)
    """
    return f"{MEMORY_LOG_PREFIX}*{MEMORY_LOG_SUFFIX}"
