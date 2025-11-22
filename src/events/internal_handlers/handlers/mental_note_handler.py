"""
Mental note storage event handler.

Handles mental_note.stored events by storing vectors in ChromaDB
and updating PostgreSQL with embeddings.
"""

from typing import Dict, Any, Optional, Tuple, List
from .base_handler import BaseStorageHandler
from ..config import InternalHandlerConfig



class MentalNoteStorageHandler(BaseStorageHandler):
    """
    Event handler for mental note storage operations.

    Decouples vector storage from main request flow,
    allowing async background processing and non-blocking failures.

    With per-project isolation, creates VectorStorageService dynamically
    for each event based on user_id and project_id.
    """

    def __init__(self, *args, **kwargs):
        """Initialize handler with file storage support"""
        super().__init__(*args, **kwargs)
        # Initialize file storage for saving mental notes as JSON


    def _get_log_prefix(self) -> str:
        """Get log prefix for mental note handler"""
        return InternalHandlerConfig.MENTAL_NOTE_PREFIX

    def _get_doc_type(self) -> str:
        """Get document type name"""
        return "mental_note"

    def _get_doc_id_field(self) -> str:
        """Get document ID field name"""
        return InternalHandlerConfig.MENTAL_NOTE_ID_FIELD

    def _get_doc_id(self, validated: Dict[str, Any]) -> int:
        """Get mental note ID from validated data"""
        return validated["mental_note_id"]

    def _extract_and_validate(self, event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract and validate mental note event data.

        Args:
            event_data: Raw event payload

        Returns:
            Validated data dict or None if validation fails
        """
        validated = self.validator.extract_mental_note_data(event_data)

        if not validated:
            # Log specific reason for failure
            user_id = event_data.get(InternalHandlerConfig.USER_ID_FIELD)
            project_id = event_data.get(InternalHandlerConfig.PROJECT_ID_FIELD)
            mental_note_id = event_data.get(InternalHandlerConfig.MENTAL_NOTE_ID_FIELD)

            if not user_id or not project_id:
                message = self.formatter.format_validation_error(
                    self._get_log_prefix(),
                    "user_id or project_id not provided"
                )
                self.logger.warning(message)
            elif not mental_note_id:
                message = self.formatter.format_validation_error(
                    self._get_log_prefix(),
                    "mental_note_id not found in event data"
                )
                self.logger.error(message)

        return validated

    async def _store_vector(self, validated: Dict[str, Any]) -> Tuple[str, List[float]]:
        """
        Store mental note vector in ChromaDB.

        Args:
            validated: Validated event data

        Returns:
            Tuple of (note_id from ChromaDB, embedding vector)
        """
        # Log before calling vector service
        self.logger.info(
            self.formatter.format_calling_store(
                self._get_log_prefix(),
                "store_mental_note_vector"
            )
        )

        note_id, embedding = await self.orchestrator.store_mental_note_vector(
            mental_note_id=validated["mental_note_id"],
            content=validated["content"],
            user_id=validated["user_id"],
            project_id=validated["project_id"]
        )

        return note_id, embedding

    def _log_vector_stored(
        self,
        vector_id: str,
        validated: Dict[str, Any],
        embedding: List[float]
    ):
        """
        Override to log mental note specific format with embedding dimensions.

        Args:
            vector_id: Vector ID from ChromaDB
            validated: Validated event data
            embedding: Embedding vector
        """
        # Mental note uses specific format with embedding dimensions
        message = self.formatter.format_mental_note_stored(
            self._get_log_prefix(),
            vector_id,
            len(embedding)
        )
        self.logger.info(message)

    async def _update_database(self, validated: Dict[str, Any], embedding: List[float]):
        """
        Update PostgreSQL with embedding.

        Args:
            validated: Validated event data
            embedding: Embedding vector to store
        """
        mental_note_id = validated["mental_note_id"]

        success = await self.db_updater.update_mental_note(
            mental_note_id=mental_note_id,
            embedding=embedding,
            user_id=validated["user_id"],
            project_id=validated["project_id"]
        )

        if success:
            message = self.formatter.format_postgres_updated(
                self._get_log_prefix(),
                mental_note_id,
                self._get_doc_type()
            )
            self.logger.info(message)

    async def handle_stored_event(self, event_data: Dict[str, Any]):
        """
        Override template method to add file storage step.

        This extends the base handler workflow with JSON file storage.
        """
        try:
            # Step 1: Log event reception
            self._log_event_received(event_data)

            # Step 2: Extract and validate
            validated = self._extract_and_validate(event_data)
            if not validated:
                return

            # Step 3: Log processing details
            self._log_processing_details(validated)

            # Step 4: Store vector in ChromaDB
            vector_id, embedding = await self._store_vector(validated)

            # Step 5: Log vector storage success
            self._log_vector_stored(vector_id, validated, embedding)

            # Step 6: Update PostgreSQL with embedding
            await self._update_database(validated, embedding)



        except Exception as e:
            self._handle_error(e, event_data)



    async def handle_mental_note_stored(self, event_data: Dict[str, Any]):
        """
        Handle mental_note.stored event for vector storage.

        Generates embeddings and stores in ChromaDB after PostgreSQL storage completes.

        Args:
            event_data: Event payload containing mental note data and ID
        """
        await self.handle_stored_event(event_data)
