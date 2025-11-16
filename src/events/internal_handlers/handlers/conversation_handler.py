"""
Conversation storage event handler.

Handles conversation.stored events by storing vectors in separate ChromaDB collection
and updating PostgreSQL with embeddings.
"""

from typing import Dict, Any, Optional, Tuple, List
from .base_handler import BaseStorageHandler
from ..config import InternalHandlerConfig


class ConversationStorageHandler(BaseStorageHandler):
    """
    Event handler for conversation storage operations.

    Stores conversations in separate conversations_{hash} ChromaDB collection,
    isolated from memory_logs and mental_notes.

    Decouples vector storage from main request flow,
    allowing async background processing and non-blocking failures.
    """

    def _get_log_prefix(self) -> str:
        """Get log prefix for conversation handler"""
        return "[CONVERSATION_HANDLER]"

    def _get_doc_type(self) -> str:
        """Get document type name"""
        return "conversation"

    def _get_doc_id_field(self) -> str:
        """Get document ID field name"""
        return "conversation_db_id"

    def _get_doc_id(self, validated: Dict[str, Any]) -> int:
        """Get conversation database ID from validated data"""
        return validated["conversation_db_id"]

    def _extract_and_validate(self, event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract and validate conversation event data.

        Args:
            event_data: Raw event payload from conversation.stored event

        Returns:
            Validated data dict or None if validation fails
        """
        user_id = event_data.get("user_id")
        project_id = event_data.get("project_id")
        conversation_db_id = event_data.get("conversation_db_id")
        raw_data = event_data.get("raw_data")

        # Validation
        if not user_id or not project_id:
            self.logger.warning(
                f"{self._get_log_prefix()} Validation failed: user_id or project_id not provided"
            )
            return None

        if not conversation_db_id:
            self.logger.error(
                f"{self._get_log_prefix()} Validation failed: conversation_db_id not found"
            )
            return None

        if not raw_data:
            self.logger.error(
                f"{self._get_log_prefix()} Validation failed: raw_data not found"
            )
            return None

        # Ensure conversation messages exist
        conversation_messages = raw_data.get("conversation", [])
        if not conversation_messages:
            self.logger.error(
                f"{self._get_log_prefix()} Validation failed: conversation has no messages"
            )
            return None

        return {
            "conversation_db_id": conversation_db_id,
            "user_id": user_id,
            "project_id": project_id,
            "raw_data": raw_data
        }

    async def _store_vector(self, validated: Dict[str, Any]) -> Tuple[str, List[float]]:
        """
        Store conversation vector in separate ChromaDB collection.

        Args:
            validated: Validated event data

        Returns:
            Tuple of (conversation_id from ChromaDB, embedding vector)
        """
        self.logger.info(
            f"{self._get_log_prefix()} Calling store_conversation_vector"
        )

        conversation_id, embedding = await self.orchestrator.store_conversation_vector(
            conversation_db_id=validated["conversation_db_id"],
            raw_data=validated["raw_data"],
            user_id=validated["user_id"]
        )

        return conversation_id, embedding

    async def _update_database(self, validated: Dict[str, Any], embedding: List[float]):
        """
        Skip PostgreSQL embedding update for conversations.

        Conversations do NOT store embeddings in PostgreSQL (no pgvector dependency).
        Embeddings are ONLY stored in ChromaDB for semantic search.

        Args:
            validated: Validated event data
            embedding: Embedding vector (not used for conversations)
        """
        conversation_db_id = validated["conversation_db_id"]

        self.logger.info(
            f"{self._get_log_prefix()} Skipping PostgreSQL embedding update for conversation {conversation_db_id} "
            "(embeddings stored only in ChromaDB)"
        )

    async def handle_conversation_stored(self, event_data: Dict[str, Any]):
        """
        Handle conversation.stored event for vector storage.

        Workflow:
        1. Extract and validate event data
        2. Create VectorStorageService for user/project
        3. Generate embedding and store in conversations_{hash} collection
        4. Update PostgreSQL with embedding

        Args:
            event_data: Event payload containing conversation data
        """
        await self.handle_stored_event(event_data)
