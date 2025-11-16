"""
Conversation File Storage

Stores conversation JSON files in organized folder structure:
data/users/user_{user_id}/conversations/conversation_{conversation_id}.json

This provides direct file access to conversations alongside ChromaDB vector storage.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from src.modules.core.telemetry.logger import get_logger

logger = get_logger(__name__)


class ConversationFileStorage:
    """
    File-based storage for conversation JSON data.

    Folder structure:
    data/users/user_{user_id}/conversations/conversation_{conversation_id}.json

    Features:
    - Automatic directory creation
    - Pretty-printed JSON (indent=2)
    - Error handling with logging
    - Non-blocking (errors don't fail requests)
    """

    def __init__(self, base_path: str = "./data/users"):
        """
        Initialize conversation file storage.

        Args:
            base_path: Base directory for user data (default: ./data/users)
        """
        self.base_path = Path(base_path)
        self.logger = logger

    def _get_user_conversations_dir(self, user_id: str) -> Path:
        """
        Get the conversations directory path for a user.

        Args:
            user_id: User identifier

        Returns:
            Path to user's conversations directory
        """
        return self.base_path / f"user_{user_id}" / "conversations"

    def _get_conversation_file_path(self, user_id: str, conversation_id: str) -> Path:
        """
        Get the file path for a specific conversation.

        Args:
            user_id: User identifier
            conversation_id: Conversation identifier (UUID)

        Returns:
            Path to conversation JSON file
        """
        conversations_dir = self._get_user_conversations_dir(user_id)
        return conversations_dir / f"conversation_{conversation_id}.json"

    def _ensure_directory_exists(self, user_id: str) -> bool:
        """
        Ensure the user's conversations directory exists.

        Args:
            user_id: User identifier

        Returns:
            True if directory exists or was created, False on error
        """
        try:
            conversations_dir = self._get_user_conversations_dir(user_id)
            conversations_dir.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"[FILE_STORAGE] Ensured directory exists: {conversations_dir}")
            return True
        except Exception as e:
            self.logger.error(f"[FILE_STORAGE] Failed to create directory for user {user_id}: {e}")
            return False

    def save_conversation(
        self,
        user_id: str,
        conversation_id: str,
        conversation_data: Dict[str, Any]
    ) -> bool:
        """
        Save conversation data to JSON file.

        Creates directory structure if needed:
        data/users/user_{user_id}/conversations/conversation_{conversation_id}.json

        Args:
            user_id: User identifier
            conversation_id: Conversation identifier (UUID)
            conversation_data: Complete conversation data dictionary

        Returns:
            True if saved successfully, False on error
        """
        try:
            # Ensure directory exists
            if not self._ensure_directory_exists(user_id):
                return False

            # Get file path
            file_path = self._get_conversation_file_path(user_id, conversation_id)

            # Write JSON file with pretty formatting
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(conversation_data, f, indent=2, ensure_ascii=False)

            self.logger.info(
                f"[FILE_STORAGE] Saved conversation to file: {file_path} "
                f"(user: {user_id}, conversation: {conversation_id})"
            )
            return True

        except Exception as e:
            self.logger.error(
                f"[FILE_STORAGE] Failed to save conversation {conversation_id} for user {user_id}: {e}",
                exc_info=True
            )
            return False

    def load_conversation(
        self,
        user_id: str,
        conversation_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Load conversation data from JSON file.

        Args:
            user_id: User identifier
            conversation_id: Conversation identifier (UUID)

        Returns:
            Conversation data dictionary or None if not found/error
        """
        try:
            file_path = self._get_conversation_file_path(user_id, conversation_id)

            if not file_path.exists():
                self.logger.warning(
                    f"[FILE_STORAGE] Conversation file not found: {file_path}"
                )
                return None

            # Read JSON file
            with open(file_path, 'r', encoding='utf-8') as f:
                conversation_data = json.load(f)

            self.logger.debug(
                f"[FILE_STORAGE] Loaded conversation from file: {file_path}"
            )
            return conversation_data

        except Exception as e:
            self.logger.error(
                f"[FILE_STORAGE] Failed to load conversation {conversation_id} for user {user_id}: {e}",
                exc_info=True
            )
            return None

    def delete_conversation(
        self,
        user_id: str,
        conversation_id: str
    ) -> bool:
        """
        Delete conversation JSON file.

        Args:
            user_id: User identifier
            conversation_id: Conversation identifier (UUID)

        Returns:
            True if deleted successfully, False on error or not found
        """
        try:
            file_path = self._get_conversation_file_path(user_id, conversation_id)

            if not file_path.exists():
                self.logger.warning(
                    f"[FILE_STORAGE] Cannot delete, file not found: {file_path}"
                )
                return False

            # Delete file
            file_path.unlink()

            self.logger.info(
                f"[FILE_STORAGE] Deleted conversation file: {file_path}"
            )
            return True

        except Exception as e:
            self.logger.error(
                f"[FILE_STORAGE] Failed to delete conversation {conversation_id} for user {user_id}: {e}",
                exc_info=True
            )
            return False

    def list_conversations(self, user_id: str) -> List[str]:
        """
        List all conversation IDs for a user.

        Args:
            user_id: User identifier

        Returns:
            List of conversation IDs (UUIDs extracted from filenames)
        """
        try:
            conversations_dir = self._get_user_conversations_dir(user_id)

            if not conversations_dir.exists():
                self.logger.debug(
                    f"[FILE_STORAGE] Conversations directory does not exist for user {user_id}"
                )
                return []

            # Find all conversation_*.json files
            conversation_files = conversations_dir.glob("conversation_*.json")

            # Extract conversation IDs from filenames
            conversation_ids = []
            for file_path in conversation_files:
                # Remove "conversation_" prefix and ".json" suffix
                filename = file_path.stem  # Gets filename without extension
                if filename.startswith("conversation_"):
                    conversation_id = filename[len("conversation_"):]
                    conversation_ids.append(conversation_id)

            self.logger.debug(
                f"[FILE_STORAGE] Found {len(conversation_ids)} conversations for user {user_id}"
            )
            return conversation_ids

        except Exception as e:
            self.logger.error(
                f"[FILE_STORAGE] Failed to list conversations for user {user_id}: {e}",
                exc_info=True
            )
            return []

    def conversation_exists(self, user_id: str, conversation_id: str) -> bool:
        """
        Check if a conversation file exists.

        Args:
            user_id: User identifier
            conversation_id: Conversation identifier (UUID)

        Returns:
            True if file exists, False otherwise
        """
        file_path = self._get_conversation_file_path(user_id, conversation_id)
        return file_path.exists()
