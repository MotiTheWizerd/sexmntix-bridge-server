"""
Memory log storage event handler.

Handles memory_log.stored events by storing vectors in ChromaDB
and updating PostgreSQL with embeddings.
"""

from typing import Dict, Any, Optional, Tuple, List
from .base_handler import BaseStorageHandler
from ..config import InternalHandlerConfig


class MemoryLogStorageHandler(BaseStorageHandler):
    """
    Event handler for memory log storage operations.

    Decouples vector storage from main request flow,
    allowing async background processing and non-blocking failures.

    With per-project isolation, creates VectorStorageService dynamically
    for each event based on user_id and project_id.
    """

    def _get_log_prefix(self) -> str:
        """Get log prefix for memory log handler"""
        return InternalHandlerConfig.MEMORY_LOG_PREFIX

    def _get_doc_type(self) -> str:
        """Get document type name"""
        return "memory_log"

    def _get_doc_id_field(self) -> str:
        """Get document ID field name"""
        return InternalHandlerConfig.MEMORY_LOG_ID_FIELD

    def _get_doc_id(self, validated: Dict[str, Any]) -> int:
        """Get memory log ID from validated data"""
        return validated["memory_log_id"]

    def _extract_and_validate(self, event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract and validate memory log event data.

        Args:
            event_data: Raw event payload

        Returns:
            Validated data dict or None if validation fails
        """
        validated = self.validator.extract_memory_log_data(event_data)

        if not validated:
            # Log specific reason for failure
            user_id = event_data.get(InternalHandlerConfig.USER_ID_FIELD)
            project_id = event_data.get(InternalHandlerConfig.PROJECT_ID_FIELD)
            memory_log_id = event_data.get(InternalHandlerConfig.MEMORY_LOG_ID_FIELD)

            if not user_id or not project_id:
                message = self.formatter.format_validation_error(
                    self._get_log_prefix(),
                    "user_id or project_id not provided"
                )
                self.logger.warning(message)
            elif not memory_log_id:
                message = self.formatter.format_validation_error(
                    self._get_log_prefix(),
                    "memory_log_id not found in event data"
                )
                self.logger.error(message)

        return validated

    async def _store_vector(self, validated: Dict[str, Any]) -> Tuple[str, List[float]]:
        """
        Store memory log vector in ChromaDB.

        Args:
            validated: Validated event data

        Returns:
            Tuple of (memory_id from ChromaDB, embedding vector)
        """
        # Log before calling vector service
        self.logger.info(
            self.formatter.format_calling_store(
                self._get_log_prefix(),
                "store_memory_vector"
            )
        )

        memory_id, embedding = await self.orchestrator.store_memory_vector(
            memory_log_id=validated["memory_log_id"],
            raw_data=validated["raw_data"],
            user_id=validated["user_id"],
            project_id=validated["project_id"]
        )

        return memory_id, embedding

    async def _update_database(self, validated: Dict[str, Any], embedding: List[float]):
        """
        Update PostgreSQL with embedding.

        Args:
            validated: Validated event data
            embedding: Embedding vector to store
        """
        memory_log_id = validated["memory_log_id"]

        success = await self.db_updater.update_memory_log(
            memory_log_id=memory_log_id,
            embedding=embedding
        )

        if success:
            message = self.formatter.format_postgres_updated(
                self._get_log_prefix(),
                memory_log_id,
                self._get_doc_type()
            )
            self.logger.info(message)

    async def handle_memory_log_stored(self, event_data: Dict[str, Any]):
        """
        Handle memory_log.stored event for vector storage.

        Generates embeddings and stores in ChromaDB after PostgreSQL storage completes.

        Args:
            event_data: Event payload containing memory log data and ID
        """
        await self.handle_stored_event(event_data)
