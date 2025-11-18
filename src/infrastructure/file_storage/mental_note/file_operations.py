"""
File Operations for Mental Note Storage

Handles low-level file I/O operations for mental note JSON files.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from src.modules.core.telemetry.logger import get_logger

logger = get_logger(__name__)


class MentalNoteFileOperations:
    """
    Low-level file I/O operations for mental note JSON files.

    Responsibilities:
    - Read JSON files
    - Write JSON files with pretty formatting
    - Delete files
    - Handle encoding and error logging
    """

    @staticmethod
    def write_json(file_path: Path, data: Dict[str, Any]) -> bool:
        """
        Write data to JSON file with pretty formatting.

        Args:
            file_path: Path to JSON file
            data: Data to write

        Returns:
            True if successful, False on error
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.debug(f"[MENTAL_NOTE_FILE_OPS] Successfully wrote JSON to: {file_path}")
            return True

        except Exception as e:
            logger.error(
                f"[MENTAL_NOTE_FILE_OPS] Failed to write JSON to {file_path}: {e}",
                exc_info=True
            )
            return False

    @staticmethod
    def read_json(file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Read data from JSON file.

        Args:
            file_path: Path to JSON file

        Returns:
            Data dictionary or None if not found/error
        """
        try:
            if not file_path.exists():
                logger.warning(f"[MENTAL_NOTE_FILE_OPS] File not found: {file_path}")
                return None

            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            logger.debug(f"[MENTAL_NOTE_FILE_OPS] Successfully read JSON from: {file_path}")
            return data

        except Exception as e:
            logger.error(
                f"[MENTAL_NOTE_FILE_OPS] Failed to read JSON from {file_path}: {e}",
                exc_info=True
            )
            return None

    @staticmethod
    def delete_file(file_path: Path) -> bool:
        """
        Delete a file.

        Args:
            file_path: Path to file

        Returns:
            True if deleted successfully, False on error or not found
        """
        try:
            if not file_path.exists():
                logger.warning(f"[MENTAL_NOTE_FILE_OPS] Cannot delete, file not found: {file_path}")
                return False

            file_path.unlink()
            logger.debug(f"[MENTAL_NOTE_FILE_OPS] Successfully deleted file: {file_path}")
            return True

        except Exception as e:
            logger.error(
                f"[MENTAL_NOTE_FILE_OPS] Failed to delete file {file_path}: {e}",
                exc_info=True
            )
            return False
