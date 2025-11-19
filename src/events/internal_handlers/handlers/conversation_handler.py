"""
Conversation storage event handler.

Handles conversation.analyzed events by storing vectors in separate ChromaDB collection.
This fires AFTER SXThalamus has processed conversations with Gemini.
"""

from typing import Dict, Any, Optional, Tuple, List
from .base_handler import BaseStorageHandler
from ..config import InternalHandlerConfig
from src.infrastructure.file_storage import ConversationFileStorage


class ConversationStorageHandler(BaseStorageHandler):
    """
    Event handler for conversation storage operations.

    Stores conversations in separate conversations_{hash} ChromaDB collection,
    isolated from memory_logs and mental_notes.

    Decouples vector storage from main request flow,
    allowing async background processing and non-blocking failures.
    """

    def __init__(self, *args, **kwargs):
        """Initialize handler with file storage support"""
        super().__init__(*args, **kwargs)
        # Initialize file storage for saving conversations as JSON
        self.file_storage = ConversationFileStorage()

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

        # Extract Gemini analysis (required for embedding)
        gemini_analysis = event_data.get("gemini_analysis", [])
        
        # Parse if it's a JSON string
        if isinstance(gemini_analysis, str):
            import json
            import re
            
            # Log what we received for debugging
            self.logger.info(
                f"{self._get_log_prefix()} Received gemini_analysis as string, "
                f"length: {len(gemini_analysis)}, preview: {gemini_analysis[:200]}"
            )
            
            try:
                # Strip markdown code blocks if present (```json ... ```)
                cleaned = gemini_analysis.strip()
                if cleaned.startswith("```"):
                    # Remove markdown code fence
                    cleaned = re.sub(r'^```(?:json)?\s*\n', '', cleaned)
                    cleaned = re.sub(r'\n```\s*$', '', cleaned)
                
                gemini_analysis = json.loads(cleaned)
                self.logger.info(
                    f"{self._get_log_prefix()} Successfully parsed {len(gemini_analysis)} memory units"
                )
            except json.JSONDecodeError as e:
                self.logger.error(
                    f"{self._get_log_prefix()} Failed to parse gemini_analysis JSON: {e}"
                )
                self.logger.error(
                    f"{self._get_log_prefix()} Raw content (first 500 chars): {gemini_analysis[:500]}"
                )
                gemini_analysis = []

        return {
            "conversation_db_id": conversation_db_id,
            "user_id": user_id,
            "project_id": project_id,
            "raw_data": raw_data,
            "gemini_analysis": gemini_analysis
        }

    async def _store_vector(self, validated: Dict[str, Any]) -> Tuple[List[str], List[List[float]]]:
        """
        Store conversation memory units in separate ChromaDB collection.

        Args:
            validated: Validated event data with gemini_analysis

        Returns:
            Tuple of (list of conversation_ids, list of embedding vectors)
        """
        self.logger.info(
            f"{self._get_log_prefix()} Calling store_conversation_vector with "
            f"{len(validated.get('gemini_analysis', []))} memory units"
        )

        conversation_ids, embeddings = await self.orchestrator.store_conversation_vector(
            conversation_db_id=validated["conversation_db_id"],
            raw_data=validated["raw_data"],
            user_id=validated["user_id"],
            gemini_analysis=validated.get("gemini_analysis", [])
        )

        return conversation_ids, embeddings

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

            # Step 4: Store vectors in ChromaDB (multiple memory units)
            vector_ids, embeddings = await self._store_vector(validated)

            # Step 5: Log vector storage success
            if vector_ids:
                self.logger.info(
                    f"{self._get_log_prefix()} Stored {len(vector_ids)} memory units in ChromaDB"
                )
            else:
                self.logger.warning(
                    f"{self._get_log_prefix()} No memory units stored (no Gemini analysis)"
                )

            # Step 6: Update PostgreSQL with embedding (skipped for conversations)
            # Conversations don't store embeddings in PostgreSQL
            await self._update_database(validated, embeddings[0] if embeddings else [])

            # Step 7: Save to JSON file (NEW STEP)
            self._save_to_file(validated)

        except Exception as e:
            self._handle_error(e, event_data)

    def _save_to_file(self, validated: Dict[str, Any]) -> None:
        """
        Save conversation to JSON file in users folder.

        Args:
            validated: Validated event data
        """
        try:
            conversation_db_id = validated["conversation_db_id"]
            user_id = validated["user_id"]
            project_id = validated["project_id"]
            raw_data = validated["raw_data"]

            # Extract conversation_id from raw_data
            conversation_id = raw_data.get("conversation_id")
            if not conversation_id:
                self.logger.warning(
                    f"{self._get_log_prefix()} No conversation_id in raw_data, "
                    f"cannot save to file for conversation DB ID {conversation_db_id}"
                )
                return

            # Prepare conversation data for JSON file
            conversation_data = {
                "user_id": user_id,
                "project_id": project_id,
                **raw_data  # Include all fields from raw_data
            }

            # Save to JSON file
            success = self.file_storage.save_conversation(
                user_id=str(user_id),
                conversation_id=conversation_id,
                conversation_data=conversation_data
            )

            if success:
                self.logger.info(
                    f"{self._get_log_prefix()} Successfully saved conversation {conversation_id} "
                    f"to JSON file for user {user_id}"
                )
            else:
                self.logger.warning(
                    f"{self._get_log_prefix()} Failed to save conversation {conversation_id} "
                    f"to JSON file for user {user_id}"
                )

        except Exception as e:
            # Log error but don't fail the entire operation
            self.logger.error(
                f"{self._get_log_prefix()} Error saving conversation to file: {e}",
                exc_info=True
            )

    async def handle_conversation_analyzed(self, event_data: Dict[str, Any]):
        """
        Handle conversation.analyzed event for vector storage.

        This fires AFTER SXThalamus has processed the conversation with Gemini.

        Workflow:
        1. Extract and validate event data
        2. Create VectorStorageService for user/project
        3. Generate embedding and store in conversations_{hash} collection
        4. Skip PostgreSQL embedding update (embeddings only in ChromaDB)

        Args:
            event_data: Event payload containing:
                - conversation_db_id: PostgreSQL ID
                - conversation_id: UUID
                - model: AI model name
                - raw_data: Original conversation data
                - user_id, project_id: Identifiers
                - gemini_analysis: Processed output from Gemini
                - original_combined_text: Original combined message text
        """
        await self.handle_stored_event(event_data)
