"""
Path Builder for Mental Note Storage

Pure functions for building paths (no I/O, stateless, easily testable).
"""

from pathlib import Path


def build_user_mental_notes_dir(base_path: Path, user_id: str) -> Path:
    """
    Build path to user's mental_notes directory.

    Args:
        base_path: Base directory (e.g., ./data/users)
        user_id: User identifier

    Returns:
        Path: data/users/user_{user_id}/mental_notes
    """
    return base_path / f"user_{user_id}" / "mental_notes"


def build_mental_note_file_path(base_path: Path, user_id: str, mental_note_id: int) -> Path:
    """
    Build full file path for a mental note JSON file.

    Args:
        base_path: Base directory (e.g., ./data/users)
        user_id: User identifier
        mental_note_id: Mental note ID

    Returns:
        Path: data/users/user_{user_id}/mental_notes/mental_note_{mental_note_id}.json
    """
    mental_notes_dir = build_user_mental_notes_dir(base_path, user_id)
    return mental_notes_dir / f"mental_note_{mental_note_id}.json"


def get_glob_pattern() -> str:
    """
    Get glob pattern for matching mental note files.

    Returns:
        Glob pattern string (e.g., "mental_note_*.json")
    """
    return "mental_note_*.json"
