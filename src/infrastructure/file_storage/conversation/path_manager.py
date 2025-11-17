"""
Path Manager for Conversation Storage

Handles all path generation and directory management for conversation files.
"""

from pathlib import Path
from typing import List
from src.modules.core.telemetry.logger import get_logger

logger = get_logger(__name__)


class ConversationPathManager:
    """
    Manages file paths and directories for conversation storage.

    Responsibilities:
    - Generate paths for user directories and conversation files
    - Create and ensure directories exist
    - List conversation files
    """

    def __init__(self, base_path: str = "./data/users"):
        """
        Initialize path manager.

        Args:
            base_path: Base directory for user data (default: ./data/users)
        """
        self.base_path = Path(base_path)

    def get_user_conversations_dir(self, user_id: str) -> Path:
        """
        Get the conversations directory path for a user.

        Args:
            user_id: User identifier

        Returns:
            Path to user's conversations directory
        """
        return self.base_path / f"user_{user_id}" / "conversations"

    def get_conversation_file_path(self, user_id: str, conversation_id: str) -> Path:
        """
        Get the file path for a specific conversation.

        Args:
            user_id: User identifier
            conversation_id: Conversation identifier (UUID)

        Returns:
            Path to conversation JSON file
        """
        conversations_dir = self.get_user_conversations_dir(user_id)
        return conversations_dir / f"conversation_{conversation_id}.json"

    def ensure_directory_exists(self, user_id: str) -> bool:
        """
        Ensure the user's conversations directory exists.

        Args:
            user_id: User identifier

        Returns:
            True if directory exists or was created, False on error
        """
        try:
            conversations_dir = self.get_user_conversations_dir(user_id)
            conversations_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"[CONVERSATION_PATH_MANAGER] Ensured directory exists: {conversations_dir}")
            return True
        except Exception as e:
            logger.error(f"[CONVERSATION_PATH_MANAGER] Failed to create directory for user {user_id}: {e}")
            return False

    def list_conversation_files(self, user_id: str) -> List[Path]:
        """
        List all conversation files for a user.

        Args:
            user_id: User identifier

        Returns:
            List of Path objects for conversation files
        """
        conversations_dir = self.get_user_conversations_dir(user_id)

        if not conversations_dir.exists():
            logger.debug(
                f"[CONVERSATION_PATH_MANAGER] Conversations directory does not exist for user {user_id}"
            )
            return []

        return list(conversations_dir.glob("conversation_*.json"))

    def extract_conversation_id(self, file_path: Path) -> str | None:
        """
        Extract conversation ID from filename.

        Args:
            file_path: Path to conversation file

        Returns:
            Conversation ID (UUID) or None if invalid filename
        """
        filename = file_path.stem
        if filename.startswith("conversation_"):
            conversation_id = filename[len("conversation_"):]
            return conversation_id if conversation_id else None
        return None

    def file_exists(self, user_id: str, conversation_id: str) -> bool:
        """
        Check if a conversation file exists.

        Args:
            user_id: User identifier
            conversation_id: Conversation identifier (UUID)

        Returns:
            True if file exists, False otherwise
        """
        file_path = self.get_conversation_file_path(user_id, conversation_id)
        return file_path.exists()
