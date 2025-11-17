"""
Memory Log File Storage

Main orchestrator for memory log file storage operations.
"""

from typing import Dict, Any, Optional, List
from src.modules.core.telemetry.logger import get_logger
from .path_manager import MemoryLogPathManager
from .file_operations import MemoryLogFileOperations

logger = get_logger(__name__)


class MemoryLogFileStorage:
    """
    File-based storage for memory log JSON data.

    Folder structure:
    data/users/user_{user_id}/memory_logs/memory_{memory_log_id}.json

    Features:
    - Automatic directory creation
    - Pretty-printed JSON (indent=2)
    - Error handling with logging
    - Non-blocking (errors don't fail requests)
    """

    def __init__(self, base_path: str = "./data/users"):
        """
        Initialize memory log file storage.

        Args:
            base_path: Base directory for user data (default: ./data/users)
        """
        self.path_manager = MemoryLogPathManager(base_path)
        self.file_ops = MemoryLogFileOperations()
        self.logger = logger

    def save_memory_log(
        self,
        user_id: str,
        memory_log_id: int,
        memory_log_data: Dict[str, Any]
    ) -> bool:
        """
        Save memory log data to JSON file.

        Creates directory structure if needed:
        data/users/user_{user_id}/memory_logs/memory_{memory_log_id}.json

        Args:
            user_id: User identifier
            memory_log_id: Memory log ID
            memory_log_data: Complete memory log data dictionary

        Returns:
            True if saved successfully, False on error
        """
        # Ensure directory exists
        if not self.path_manager.ensure_directory_exists(user_id):
            return False

        # Get file path
        file_path = self.path_manager.get_memory_log_file_path(user_id, memory_log_id)

        # Write JSON file
        success = self.file_ops.write_json(file_path, memory_log_data)

        if success:
            self.logger.info(
                f"[MEMORY_FILE_STORAGE] Saved memory log to file: {file_path} "
                f"(user: {user_id}, memory_log_id: {memory_log_id})"
            )

        return success

    def load_memory_log(
        self,
        user_id: str,
        memory_log_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Load memory log data from JSON file.

        Args:
            user_id: User identifier
            memory_log_id: Memory log ID

        Returns:
            Memory log data dictionary or None if not found/error
        """
        file_path = self.path_manager.get_memory_log_file_path(user_id, memory_log_id)
        memory_log_data = self.file_ops.read_json(file_path)

        if memory_log_data:
            self.logger.debug(
                f"[MEMORY_FILE_STORAGE] Loaded memory log from file: {file_path}"
            )

        return memory_log_data

    def delete_memory_log(
        self,
        user_id: str,
        memory_log_id: int
    ) -> bool:
        """
        Delete memory log JSON file.

        Args:
            user_id: User identifier
            memory_log_id: Memory log ID

        Returns:
            True if deleted successfully, False on error or not found
        """
        file_path = self.path_manager.get_memory_log_file_path(user_id, memory_log_id)
        success = self.file_ops.delete_file(file_path)

        if success:
            self.logger.info(
                f"[MEMORY_FILE_STORAGE] Deleted memory log file: {file_path}"
            )

        return success

    def list_memory_logs(self, user_id: str) -> List[int]:
        """
        List all memory log IDs for a user.

        Args:
            user_id: User identifier

        Returns:
            List of memory log IDs (extracted from filenames)
        """
        try:
            # Get all memory log files
            memory_log_files = self.path_manager.list_memory_log_files(user_id)

            # Extract memory log IDs from filenames
            memory_log_ids = []
            for file_path in memory_log_files:
                memory_log_id = self.path_manager.extract_memory_log_id(file_path)
                if memory_log_id is not None:
                    memory_log_ids.append(memory_log_id)

            self.logger.debug(
                f"[MEMORY_FILE_STORAGE] Found {len(memory_log_ids)} memory logs for user {user_id}"
            )
            return sorted(memory_log_ids)

        except Exception as e:
            self.logger.error(
                f"[MEMORY_FILE_STORAGE] Failed to list memory logs for user {user_id}: {e}",
                exc_info=True
            )
            return []

    def memory_log_exists(self, user_id: str, memory_log_id: int) -> bool:
        """
        Check if a memory log file exists.

        Args:
            user_id: User identifier
            memory_log_id: Memory log ID

        Returns:
            True if file exists, False otherwise
        """
        return self.path_manager.file_exists(user_id, memory_log_id)
