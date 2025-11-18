"""
Path Manager for Mental Note Storage

Simplified orchestrator that coordinates utility functions.
All core logic has been extracted to reusable utilities in the utils/ module.
"""

from pathlib import Path
from typing import List
from .utils import (
    build_user_mental_notes_dir,
    build_mental_note_file_path,
    ensure_directory_exists,
    list_files_by_pattern,
    file_exists,
    extract_mental_note_id,
    get_glob_pattern,
)


class MentalNotePathManager:
    """
    Orchestrates path and file operations for mental note storage.

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

    def get_user_mental_notes_dir(self, user_id: str) -> Path:
        """
        Get the mental_notes directory path for a user.

        Args:
            user_id: User identifier

        Returns:
            Path to user's mental_notes directory
        """
        return build_user_mental_notes_dir(self.base_path, user_id)

    def get_mental_note_file_path(self, user_id: str, mental_note_id: int) -> Path:
        """
        Get the file path for a specific mental note.

        Args:
            user_id: User identifier
            mental_note_id: Mental note ID

        Returns:
            Path to mental note JSON file
        """
        return build_mental_note_file_path(self.base_path, user_id, mental_note_id)

    def ensure_directory_exists(self, user_id: str) -> bool:
        """
        Ensure the user's mental_notes directory exists.

        Args:
            user_id: User identifier

        Returns:
            True if directory exists or was created, False on error
        """
        mental_notes_dir = self.get_user_mental_notes_dir(user_id)
        return ensure_directory_exists(mental_notes_dir, "MENTAL_NOTE_PATH_MANAGER")

    def list_mental_note_files(self, user_id: str) -> List[Path]:
        """
        List all mental note files for a user.

        Args:
            user_id: User identifier

        Returns:
            List of Path objects for mental note files
        """
        mental_notes_dir = self.get_user_mental_notes_dir(user_id)
        pattern = get_glob_pattern()
        return list_files_by_pattern(mental_notes_dir, pattern, "MENTAL_NOTE_PATH_MANAGER")

    def extract_mental_note_id(self, file_path: Path) -> int | None:
        """
        Extract mental note ID from filename.

        Args:
            file_path: Path to mental note file

        Returns:
            Mental note ID or None if invalid filename
        """
        return extract_mental_note_id(file_path)

    def file_exists(self, user_id: str, mental_note_id: int) -> bool:
        """
        Check if a mental note file exists.

        Args:
            user_id: User identifier
            mental_note_id: Mental note ID

        Returns:
            True if file exists, False otherwise
        """
        file_path = self.get_mental_note_file_path(user_id, mental_note_id)
        return file_exists(file_path)
