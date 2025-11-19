"""
Note storage component for vector storage operations.
"""
from typing import List, Dict, Any, Optional, Tuple
from src.modules.core import EventBus, Logger
from src.modules.embeddings import EmbeddingService
from src.infrastructure.chromadb.repository import VectorRepository


class NoteStorer:
    """
    Component responsible for storing mental notes in vector storage.
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

    async def store_mental_note_vector(
        self,
        mental_note_id: int,
        mental_note_data: Dict[str, Any],
        user_id: str,
        project_id: str
    ) -> Tuple[str, List[float]]:
        """
        Generate embedding and store mental note in ChromaDB.

        Args:
            mental_note_id: Database ID of mental note
            mental_note_data: Complete mental note data (raw_data dict)
            user_id: User identifier for collection isolation
            project_id: Project identifier for collection isolation

        Returns:
            Tuple of (note_id, embedding_vector)
        """
        # Extract content from mental note data
        content = mental_note_data.get("content", "")
        note_type = mental_note_data.get("note_type", "general")
        session_id = mental_note_data.get("session_id", "")
        
        if not content.strip():
            raise ValueError(f"Mental note {mental_note_id} has no content to embed")
        
        # Generate embedding from content
        embedding_result = await self.embedding_service.generate_embedding(content)
        embedding = embedding_result.embedding

        # Convert raw data to the format expected by add_memory
        mental_note_data_for_storage = {
            "raw_data": mental_note_data,
            "content": content,
            "metadata": {
                "document_type": "mental_note",
                "mental_note_id": mental_note_id,
                "note_type": note_type,
                "session_id": session_id,
                **mental_note_data.get("metadata", {})
            }
        }

        # Store in vector repository
        note_id = await self.vector_repository.add_memory(
            memory_log_id=mental_note_id,  # Using mental_note_id as memory_log_id
            embedding=embedding,
            memory_data=mental_note_data_for_storage,
            user_id=user_id,
            project_id=project_id,
            collection_prefix="mental_notes"
        )

        # Publish event
        await self.event_bus.emit("mental_note_vector_stored", {
            "note_id": note_id,
            "mental_note_id": mental_note_id,
            "user_id": user_id,
            "project_id": project_id
        })

        return note_id, embedding
