"""
Utility functions for mental note file storage.

Pure functions extracted from path management for reusability and testing.
"""

from .path_builder import (
    build_user_mental_notes_dir,
    build_mental_note_file_path,
    get_glob_pattern,
)
from .directory_manager import ensure_directory_exists
from .file_finder import (
    list_files_by_pattern,
    file_exists,
)
from .id_parser import extract_mental_note_id

__all__ = [
    "build_user_mental_notes_dir",
    "build_mental_note_file_path",
    "get_glob_pattern",
    "ensure_directory_exists",
    "list_files_by_pattern",
    "file_exists",
    "extract_mental_note_id",
]
