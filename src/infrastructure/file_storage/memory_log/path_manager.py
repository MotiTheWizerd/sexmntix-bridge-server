"""
Path Manager for Memory Log Storage

Simplified orchestrator that coordinates utility functions.
All core logic has been extracted to reusable utilities in the utils/ module.
"""

from pathlib import Path
from typing import List
from .utils import (
    build_user_memory_logs_dir,
    build_memory_log_file_path,
    ensure_directory_exists,
    list_files_by_pattern,
    file_exists,
    extract_memory_log_id,
    get_glob_pattern,
)


class MemoryLogPathManager:
    """
    Orchestrates path and file operations for memory log storage.

    This class now delegates to utility functions for all operations,
    making it lightweight and focused on coordination.
    """

    def __init__(self, base_path: str = "./data/users"):
        """
        Initialize path manager.

        Args:
            base_path: Base directory for user data (default: ./data/users)
        """
        self.base_path = Path(base_path)

    def get_user_memory_logs_dir(self, user_id: str) -> Path:
        """
        Get the memory_logs directory path for a user.

        Args:
            user_id: User identifier

        Returns:
            Path to user's memory_logs directory
        """
        return build_user_memory_logs_dir(self.base_path, user_id)

    def get_memory_log_file_path(self, user_id: str, memory_log_id: int) -> Path:
        """
        Get the file path for a specific memory log.

        Args:
            user_id: User identifier
            memory_log_id: Memory log ID

        Returns:
            Path to memory log JSON file
        """
        return build_memory_log_file_path(self.base_path, user_id, memory_log_id)

    def ensure_directory_exists(self, user_id: str) -> bool:
        """
        Ensure the user's memory_logs directory exists.

        Args:
            user_id: User identifier

        Returns:
            True if directory exists or was created, False on error
        """
        memory_logs_dir = self.get_user_memory_logs_dir(user_id)
        return ensure_directory_exists(memory_logs_dir, "MEMORY_PATH_MANAGER")

    def list_memory_log_files(self, user_id: str) -> List[Path]:
        """
        List all memory log files for a user.

        Args:
            user_id: User identifier

        Returns:
            List of Path objects for memory log files
        """
        memory_logs_dir = self.get_user_memory_logs_dir(user_id)
        pattern = get_glob_pattern()
        return list_files_by_pattern(memory_logs_dir, pattern, "MEMORY_PATH_MANAGER")

    def extract_memory_log_id(self, file_path: Path) -> int | None:
        """
        Extract memory log ID from filename.

        Args:
            file_path: Path to memory log file

        Returns:
            Memory log ID or None if invalid filename
        """
        return extract_memory_log_id(file_path)

    def file_exists(self, user_id: str, memory_log_id: int) -> bool:
        """
        Check if a memory log file exists.

        Args:
            user_id: User identifier
            memory_log_id: Memory log ID

        Returns:
            True if file exists, False otherwise
        """
        file_path = self.get_memory_log_file_path(user_id, memory_log_id)
        return file_exists(file_path)
