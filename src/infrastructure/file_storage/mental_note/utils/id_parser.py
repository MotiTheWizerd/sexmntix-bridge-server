"""
ID Parser for Mental Note Storage

Extracts mental note IDs from file paths.
"""

import re
from pathlib import Path
from src.modules.core.telemetry.logger import get_logger

logger = get_logger(__name__)


def extract_mental_note_id(file_path: Path) -> int | None:
    """
    Extract mental note ID from filename.

    Expected format: mental_note_{id}.json

    Args:
        file_path: Path to mental note file

    Returns:
        Mental note ID (int) or None if invalid filename
    """
    try:
        # Extract filename
        filename = file_path.name

        # Pattern: mental_note_{id}.json
        match = re.match(r"mental_note_(\d+)\.json", filename)

        if match:
            mental_note_id = int(match.group(1))
            return mental_note_id

        logger.warning(f"[ID_PARSER] Invalid mental note filename format: {filename}")
        return None

    except Exception as e:
        logger.error(
            f"[ID_PARSER] Failed to extract mental note ID from {file_path}: {e}",
            exc_info=True
        )
        return None
