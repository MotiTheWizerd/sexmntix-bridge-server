"""
Conversation storage event handler.

Handles conversation.analyzed events by storing vectors in separate ChromaDB collection.
This fires AFTER SXThalamus has processed conversations with Gemini.
"""

from typing import Dict, Any, Optional, Tuple, List
from .base_handler import BaseStorageHandler
from ..config import InternalHandlerConfig
from src.services.conversation_embedding_builder import build_conversation_embedding_text
from src.modules.SXPrefrontal import CompressionBrain

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
        try:
            self.compression_brain = CompressionBrain()
        except Exception:
            self.compression_brain = None
            self.logger.warning(f"{self._get_log_prefix()} CompressionBrain unavailable; using raw turns for pgvector embedding")


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
        session_id = event_data.get("session_id")
        created_at = event_data.get("created_at")

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

        # Log raw_data structure
        import json
        self.logger.info(
            f"{self._get_log_prefix()} raw_data type: {type(raw_data)}"
        )
        self.logger.info(
            f"{self._get_log_prefix()} raw_data keys: {list(raw_data.keys()) if isinstance(raw_data, dict) else 'N/A (not a dict)'}"
        )
        self.logger.info(
            f"{self._get_log_prefix()} raw_data JSON:\n{json.dumps(raw_data, indent=2, default=str)}"
        )

        # Extract Gemini analysis (required for embedding)
        gemini_analysis = event_data.get("gemini_analysis", [])

        # Log gemini_analysis before parsing
        self.logger.info(
            f"{self._get_log_prefix()} gemini_analysis type: {type(gemini_analysis)}"
        )
        if isinstance(gemini_analysis, str):
            self.logger.info(
                f"{self._get_log_prefix()} gemini_analysis length: {len(gemini_analysis)}"
            )
            self.logger.info(
                f"{self._get_log_prefix()} gemini_analysis preview (first 500 chars): {gemini_analysis[:500]}"
            )
        elif isinstance(gemini_analysis, list):
            self.logger.info(
                f"{self._get_log_prefix()} gemini_analysis list length: {len(gemini_analysis)}"
            )
            if gemini_analysis:
                self.logger.info(
                    f"{self._get_log_prefix()} gemini_analysis first item: {json.dumps(gemini_analysis[0], indent=2, default=str)}"
                )

        # Parse if it's a JSON string
        if isinstance(gemini_analysis, str):
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
            "session_id": session_id,
            "created_at": created_at,
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
            memory_log=validated["raw_data"],
            user_id=validated["user_id"],
            session_id=validated.get("session_id"),
            gemini_analysis=validated.get("gemini_analysis", [])
        )

        return conversation_ids, embeddings

    async def _update_database(self, validated: Dict[str, Any], embedding: List[float]):
        """
        Update conversation embedding in PostgreSQL.

        Note: Conversations now support pgvector embeddings for PostgreSQL backup/redundancy.
        ChromaDB remains the source of truth for semantic search, but PostgreSQL provides
        backup and enables direct SQL-based similarity queries.

        Args:
            validated: Validated event data
            embedding: Embedding vector (768 dimensions)
        """
        conversation_db_id = validated["conversation_db_id"]

        try:
            compressed_text = build_conversation_embedding_text(
                raw_data=validated.get("raw_data"),
                created_at=validated.get("created_at"),
                compression_brain=self.compression_brain
            )

            if not compressed_text:
                self.logger.warning(
                    f"{self._get_log_prefix()} No embeddable text for conversation {conversation_db_id}, skipping pgvector update"
                )
                return

            embedding_result = await self.embedding_service.generate_embedding(compressed_text)

            success = await self.db_updater.update_conversation(
                conversation_db_id=conversation_db_id,
                embedding=embedding_result.embedding
            )

            if success:
                self.logger.info(
                    f"{self._get_log_prefix()} PostgreSQL embedding updated for conversation {conversation_db_id}"
                )
            else:
                self.logger.warning(
                    f"{self._get_log_prefix()} PostgreSQL embedding update failed for conversation {conversation_db_id} "
                    "(non-blocking, ChromaDB succeeded)"
                )
        except Exception as e:
            self.logger.warning(
                f"{self._get_log_prefix()} PostgreSQL embedding sync error for conversation {conversation_db_id}: {e} "
                "(non-blocking, ChromaDB succeeded)"
            )

    async def handle_stored_event(self, event_data: Dict[str, Any]):
        """
        Override template method to add file storage step.

        This extends the base handler workflow with JSON file storage.
        """
        try:
            # Step 0: Log complete raw JSON from client
            import json
            self.logger.info(
                f"{self._get_log_prefix()} ============ RAW CLIENT DATA START ============"
            )
            self.logger.info(
                f"{self._get_log_prefix()} Complete event_data JSON:\n{json.dumps(event_data, indent=2, default=str)}"
            )
            self.logger.info(
                f"{self._get_log_prefix()} Event data keys: {list(event_data.keys())}"
            )
            self.logger.info(
                f"{self._get_log_prefix()} ============ RAW CLIENT DATA END ============"
            )

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



        except Exception as e:
            self._handle_error(e, event_data)



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
