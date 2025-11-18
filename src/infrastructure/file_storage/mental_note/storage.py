"""
Mental Note File Storage

Main orchestrator for mental note file storage operations.
"""

from typing import Dict, Any, Optional, List
from src.modules.core.telemetry.logger import get_logger
from .path_manager import MentalNotePathManager
from .file_operations import MentalNoteFileOperations

logger = get_logger(__name__)


class MentalNoteFileStorage:
    """
    File-based storage for mental note JSON data.

    Folder structure:
    data/users/user_{user_id}/mental_notes/mental_note_{mental_note_id}.json

    Features:
    - Automatic directory creation
    - Pretty-printed JSON (indent=2)
    - Error handling with logging
    - Non-blocking (errors don't fail requests)
    """

    def __init__(self, base_path: str = "./data/users"):
        """
        Initialize mental note file storage.

        Args:
            base_path: Base directory for user data (default: ./data/users)
        """
        self.path_manager = MentalNotePathManager(base_path)
        self.file_ops = MentalNoteFileOperations()
        self.logger = logger

    def save_mental_note(
        self,
        user_id: str,
        mental_note_id: int,
        mental_note_data: Dict[str, Any]
    ) -> bool:
        """
        Save mental note data to JSON file.

        Creates directory structure if needed:
        data/users/user_{user_id}/mental_notes/mental_note_{mental_note_id}.json

        Args:
            user_id: User identifier
            mental_note_id: Mental note ID
            mental_note_data: Complete mental note data dictionary

        Returns:
            True if saved successfully, False on error
        """
        # Ensure directory exists
        if not self.path_manager.ensure_directory_exists(user_id):
            return False

        # Get file path
        file_path = self.path_manager.get_mental_note_file_path(user_id, mental_note_id)

        # Write JSON file
        success = self.file_ops.write_json(file_path, mental_note_data)

        if success:
            self.logger.info(
                f"[MENTAL_NOTE_FILE_STORAGE] Saved mental note to file: {file_path} "
                f"(user: {user_id}, mental_note_id: {mental_note_id})"
            )

        return success

    def load_mental_note(
        self,
        user_id: str,
        mental_note_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Load mental note data from JSON file.

        Args:
            user_id: User identifier
            mental_note_id: Mental note ID

        Returns:
            Mental note data dictionary or None if not found/error
        """
        file_path = self.path_manager.get_mental_note_file_path(user_id, mental_note_id)
        mental_note_data = self.file_ops.read_json(file_path)

        if mental_note_data:
            self.logger.debug(
                f"[MENTAL_NOTE_FILE_STORAGE] Loaded mental note from file: {file_path}"
            )

        return mental_note_data

    def delete_mental_note(
        self,
        user_id: str,
        mental_note_id: int
    ) -> bool:
        """
        Delete mental note JSON file.

        Args:
            user_id: User identifier
            mental_note_id: Mental note ID

        Returns:
            True if deleted successfully, False on error or not found
        """
        file_path = self.path_manager.get_mental_note_file_path(user_id, mental_note_id)
        success = self.file_ops.delete_file(file_path)

        if success:
            self.logger.info(
                f"[MENTAL_NOTE_FILE_STORAGE] Deleted mental note file: {file_path}"
            )

        return success

    def list_mental_notes(self, user_id: str) -> List[int]:
        """
        List all mental note IDs for a user.

        Args:
            user_id: User identifier

        Returns:
            List of mental note IDs (extracted from filenames)
        """
        try:
            # Get all mental note files
            mental_note_files = self.path_manager.list_mental_note_files(user_id)

            # Extract mental note IDs from filenames
            mental_note_ids = []
            for file_path in mental_note_files:
                mental_note_id = self.path_manager.extract_mental_note_id(file_path)
                if mental_note_id is not None:
                    mental_note_ids.append(mental_note_id)

            self.logger.debug(
                f"[MENTAL_NOTE_FILE_STORAGE] Found {len(mental_note_ids)} mental notes for user {user_id}"
            )
            return sorted(mental_note_ids)

        except Exception as e:
            self.logger.error(
                f"[MENTAL_NOTE_FILE_STORAGE] Failed to list mental notes for user {user_id}: {e}",
                exc_info=True
            )
            return []

    def mental_note_exists(self, user_id: str, mental_note_id: int) -> bool:
        """
        Check if a mental note file exists.

        Args:
            user_id: User identifier
            mental_note_id: Mental note ID

        Returns:
            True if file exists, False otherwise
        """
        return self.path_manager.file_exists(user_id, mental_note_id)
