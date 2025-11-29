"""
Conversation storage component for vector storage operations.
"""
from typing import List, Dict, Any, Optional, Tuple
from src.modules.core import EventBus, Logger
from src.modules.embeddings import EmbeddingService
from src.infrastructure.chromadb.repository import VectorRepository
from src.modules.vector_storage.utils import TextBuilder


class ConversationStorer:
    """
    Component responsible for storing conversations in vector storage.
    """
    def __init__(
        self,
        event_bus: EventBus,
        logger: Logger,
        embedding_service: EmbeddingService,
        vector_repository: VectorRepository
    ):
        self.event_bus = event_bus
        self.logger = logger
        self.embedding_service = embedding_service
        self.vector_repository = vector_repository
        self.text_builder = TextBuilder()

    async def store_conversation_vector(
        self,
        conversation_db_id: int,
        conversation_data: Dict[str, Any],
        user_id: str,
        project_id: str,
        session_id: Optional[str] = None,
        gemini_analysis: List[Dict[str, Any]] = None
    ) -> Tuple[List[str], List[List[float]]]:
        """
        Generate embeddings and store Gemini memory units in ChromaDB.

        Args:
            conversation_db_id: Database ID of conversation
            conversation_data: Complete conversation data (for metadata only)
            user_id: User identifier for collection isolation
            session_id: Optional session identifier for grouping conversations
            gemini_analysis: List of Gemini-enriched memory units to embed

        Returns:
            Tuple of (list of conversation_ids, list of embedding_vectors)
        """
        # Require Gemini analysis - no fallback to raw conversation
        if not gemini_analysis:
            self.logger.warning(
                f"[CONVERSATION_STORAGE] No Gemini analysis for conversation {conversation_db_id} - "
                "skipping embedding (raw conversations are not embedded)"
            )
            return [], []

        self.logger.info(
            f"[CONVERSATION_STORAGE] Processing {len(gemini_analysis)} memory units "
            f"for conversation {conversation_db_id}"
        )

        conversation_ids = []
        embeddings = []

        # Process each memory unit separately
        for idx, memory_unit in enumerate(gemini_analysis):
            # Build natural language text for embedding
            embedding_text = self.text_builder.build_embedding_text_from_memory_unit(memory_unit)

            if not embedding_text.strip():
                self.logger.warning(
                    f"[CONVERSATION_STORAGE] Memory unit {idx} has no embeddable text - skipping"
                )
                continue

            self.logger.info(
                f"[CONVERSATION_STORAGE] Generating embedding for memory unit {idx} "
                f"({len(embedding_text)} chars)"
            )

            # Generate embedding from natural language text
            embedding_result = await self.embedding_service.generate_embedding(
                embedding_text
            )
            embedding = embedding_result.embedding

            self.logger.info(
                f"[CONVERSATION_STORAGE] Embedding generated for memory unit {idx} "
                f"(dimensions: {len(embedding)}, cached: {embedding_result.cached})"
            )

            # Convert raw data to the format expected by add_memory
            metadata = {
                "document_type": "conversation_memory_unit",
                "conversation_db_id": conversation_db_id,
                "memory_index": idx,
                **memory_unit.get("metadata", {})
            }

            # Add session_id to metadata if provided
            if session_id:
                metadata["session_id"] = session_id

            memory_unit_data = {
                "raw_data": memory_unit,
                "content": embedding_text,
                "metadata": metadata
            }

            # Store in vector repository with memory unit JSON as document
            conversation_id = await self.vector_repository.add_memory(
                memory_log_id=conversation_db_id,  # Using conversation_db_id as memory_log_id
                embedding=embedding,
                memory_data=memory_unit_data,
                user_id=user_id,
                project_id=project_id,
                collection_prefix="conversations"
            )

            conversation_ids.append(conversation_id)
            embeddings.append(embedding)

            self.logger.info(
                f"[CONVERSATION_STORAGE] Memory unit {idx} stored with id: {conversation_id}"
            )

        self.logger.info(
            f"[CONVERSATION_STORAGE] Stored {len(conversation_ids)} memory units "
            f"in ChromaDB collection conversations_{{hash}}"
        )

        # Publish event
        await self.event_bus.emit("conversation_vectors_stored", {
            "conversation_db_id": conversation_db_id,
            "user_id": user_id,
            "stored_count": len(conversation_ids)
        })

        return conversation_ids, embeddings
