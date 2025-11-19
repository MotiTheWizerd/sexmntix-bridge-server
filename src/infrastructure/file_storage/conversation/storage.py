"""
Conversation File Storage

Main orchestrator for conversation file storage operations.
"""

from typing import Dict, Any, Optional, List
from src.modules.core.telemetry.logger import get_logger
from .path_manager import ConversationPathManager
from .file_operations import ConversationFileOperations

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
        self.path_manager = ConversationPathManager(base_path)
        self.file_ops = ConversationFileOperations()
        self.logger = logger

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

        If file exists, appends new messages to the conversation array.
        If file doesn't exist, creates new file with the conversation data.

        Args:
            user_id: User identifier
            conversation_id: Conversation identifier (UUID)
            conversation_data: Conversation data dictionary with 'conversation' array

        Returns:
            True if saved successfully, False on error
        """
        # Ensure directory exists
        if not self.path_manager.ensure_directory_exists(user_id):
            return False

        # Get file path
        file_path = self.path_manager.get_conversation_file_path(user_id, conversation_id)

        # Check if file already exists
        existing_data = self.file_ops.read_json(file_path)

        if existing_data:
            # File exists - append new messages to existing conversation array
            self.logger.debug(
                f"[FILE_STORAGE] Conversation file exists, appending new messages "
                f"(user: {user_id}, conversation: {conversation_id})"
            )

            # Get existing and new conversation arrays
            existing_messages = existing_data.get("conversation", [])
            new_messages = conversation_data.get("conversation", [])

            # Append new messages to existing ones
            existing_data["conversation"] = existing_messages + new_messages

            # Update other fields from new data (but keep created_at from original)
            for key, value in conversation_data.items():
                if key != "conversation" and key != "created_at":
                    existing_data[key] = value

            # Write merged data
            success = self.file_ops.write_json(file_path, existing_data)

            if success:
                self.logger.info(
                    f"[FILE_STORAGE] Appended {len(new_messages)} message(s) to conversation file: {file_path} "
                    f"(total messages: {len(existing_data['conversation'])})"
                )

        else:
            # File doesn't exist - create new file
            self.logger.debug(
                f"[FILE_STORAGE] Creating new conversation file "
                f"(user: {user_id}, conversation: {conversation_id})"
            )

            # Write new conversation file
            success = self.file_ops.write_json(file_path, conversation_data)

            if success:
                message_count = len(conversation_data.get("conversation", []))
                self.logger.info(
                    f"[FILE_STORAGE] Created new conversation file: {file_path} "
                    f"(user: {user_id}, conversation: {conversation_id}, messages: {message_count})"
                )

        return success

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
        file_path = self.path_manager.get_conversation_file_path(user_id, conversation_id)
        conversation_data = self.file_ops.read_json(file_path)

        if conversation_data:
            self.logger.debug(
                f"[FILE_STORAGE] Loaded conversation from file: {file_path}"
            )

        return conversation_data

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
        file_path = self.path_manager.get_conversation_file_path(user_id, conversation_id)
        success = self.file_ops.delete_file(file_path)

        if success:
            self.logger.info(
                f"[FILE_STORAGE] Deleted conversation file: {file_path}"
            )

        return success

    def list_conversations(self, user_id: str) -> List[str]:
        """
        List all conversation IDs for a user.

        Args:
            user_id: User identifier

        Returns:
            List of conversation IDs (UUIDs extracted from filenames)
        """
        try:
            # Get all conversation files
            conversation_files = self.path_manager.list_conversation_files(user_id)

            # Extract conversation IDs from filenames
            conversation_ids = []
            for file_path in conversation_files:
                conversation_id = self.path_manager.extract_conversation_id(file_path)
                if conversation_id is not None:
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
        return self.path_manager.file_exists(user_id, conversation_id)
