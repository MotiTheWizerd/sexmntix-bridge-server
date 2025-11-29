"""
Vector Storage Orchestrator

Single Responsibility: Orchestrate vector storage operations by delegating
to specialized micro-components.

This orchestrator acts as a facade/coordinator, composing:
- MemoryStorer: Handle memory log storage operations
- MemorySearcher: Handle memory log search operations
- MemoryRetriever: Handle memory retrieval/deletion operations
- NoteStorer: Handle mental note storage operations
- NoteSearcher: Handle mental note search operations
- ConversationStorer: Handle conversation storage operations
- ConversationSearcher: Handle conversation search operations
- TextExtractor: Extract searchable text from data
- TextBuilder: Build embedding text from memory units
"""

from typing import List, Dict, Any, Optional, Tuple
from src.modules.core import EventBus, Logger
from src.modules.embeddings import EmbeddingService
from src.infrastructure.chromadb.repository import VectorRepository

from src.modules.vector_storage.components.memory.MemoryStorer import MemoryStorer
from src.modules.vector_storage.components.memory.MemorySearcher import MemorySearcher
from src.modules.vector_storage.components.memory.MemoryRetriever import MemoryRetriever
from src.modules.vector_storage.components.mental_notes.NoteStorer import NoteStorer
from src.modules.vector_storage.components.mental_notes.NoteSearcher import NoteSearcher
from src.modules.vector_storage.components.conversations.ConversationStorer import ConversationStorer
from src.modules.vector_storage.components.conversations.ConversationSearcher import ConversationSearcher
from src.modules.vector_storage.components.text_extraction.TextExtractor import TextExtractor


class VectorStorageOrchestrator:
    """
    Orchestrator for managing vector embeddings and semantic search.

    Coordinates specialized micro-components:
    - MemoryStorer: Memory log storage operations
    - MemorySearcher: Memory log search operations
    - MemoryRetriever: Memory retrieval/deletion operations
    - NoteStorer: Mental note storage operations
    - NoteSearcher: Mental note search operations
    - ConversationStorer: Conversation storage operations
    - ConversationSearcher: Conversation search operations
    - TextExtractor: Text extraction operations

    Features:
    - Automatic embedding generation from text
    - Dual storage: PostgreSQL + ChromaDB
    - Semantic search with similarity scoring
    - Event-driven architecture
    """

    def __init__(
        self,
        event_bus: EventBus,
        logger: Logger,
        embedding_service: EmbeddingService,
        vector_repository: VectorRepository
    ):
        """
        Initialize vector storage orchestrator with micro-component composition.

        Args:
            event_bus: Event bus for publishing domain events
            logger: Logger instance
            embedding_service: Service for generating embeddings
            vector_repository: Repository for ChromaDB operations
        """
        self.event_bus = event_bus
        self.logger = logger

        # Initialize specialized micro-components
        self.memory_storer = MemoryStorer(
            event_bus=event_bus,
            logger=logger,
            embedding_service=embedding_service,
            vector_repository=vector_repository
        )

        self.memory_searcher = MemorySearcher(
            event_bus=event_bus,
            logger=logger,
            embedding_service=embedding_service,
            vector_repository=vector_repository
        )

        self.memory_retriever = MemoryRetriever(
            event_bus=event_bus,
            logger=logger,
            embedding_service=embedding_service,
            vector_repository=vector_repository
        )

        self.note_storer = NoteStorer(
            event_bus=event_bus,
            logger=logger,
            embedding_service=embedding_service,
            vector_repository=vector_repository
        )

        self.note_searcher = NoteSearcher(
            event_bus=event_bus,
            logger=logger,
            embedding_service=embedding_service,
            vector_repository=vector_repository
        )

        self.conversation_storer = ConversationStorer(
            event_bus=event_bus,
            logger=logger,
            embedding_service=embedding_service,
            vector_repository=vector_repository
        )

        self.conversation_searcher = ConversationSearcher(
            event_bus=event_bus,
            logger=logger,
            embedding_service=embedding_service,
            vector_repository=vector_repository
        )

        self.text_extractor = TextExtractor(logger)

        self.logger.info("VectorStorageOrchestrator initialized with micro-components")

    async def store_memory_vector(
        self,
        memory_log_id: int,
        memory_data: Dict[str, Any],
        user_id: str,
        project_id: str,
        text_override: Optional[str] = None
    ) -> Tuple[str, List[float]]:
        """
        Generate embedding and store in ChromaDB.

        Delegates to MemoryStorer micro-component.

        Args:
            memory_log_id: Database ID of memory log
            memory_data: Complete memory log data
            user_id: User identifier for collection isolation
            project_id: Project identifier for collection isolation
            text_override: Optional text to embed (overrides extraction)

        Returns:
            Tuple of (memory_id, embedding_vector)

        Raises:
            InvalidTextError: If searchable text is empty
            ProviderError: If embedding generation fails
        """
        return await self.memory_storer.store_memory_vector(
            memory_log_id=memory_log_id,
            memory_data=memory_data,
            user_id=user_id,
            project_id=project_id,
            text_override=text_override
        )

    async def search_similar_memories(
        self,
        query: str,
        user_id: str,
        project_id: str,
        limit: int = 10,
        where_filter: Optional[Dict[str, Any]] = None,
        min_similarity: float = 0.0,
        enable_temporal_decay: bool = False,
        half_life_days: float = 30.0
    ) -> List[Dict[str, Any]]:
        """
        Semantic search for similar memories (memory logs only).

        Filters by document_type='memory_log' to exclude mental notes.
        Delegates to MemorySearcher micro-component.

        Args:
            query: Search query text
            user_id: User identifier for collection isolation
            project_id: Project identifier for collection isolation
            limit: Maximum number of results
            where_filter: Optional metadata filter (ChromaDB where syntax)
            min_similarity: Minimum similarity threshold (0.0 to 1.0)
            enable_temporal_decay: Apply exponential decay based on memory age (default: False)
            half_life_days: Half-life in days for exponential decay (default: 30)

        Returns:
            List of search results with similarity scores
        """
        return await self.memory_searcher.search_similar_memories(
            query=query,
            user_id=user_id,
            project_id=project_id,
            limit=limit,
            where_filter=where_filter,
            min_similarity=min_similarity,
            enable_temporal_decay=enable_temporal_decay,
            half_life_days=half_life_days
        )

    async def get_memory(
        self,
        memory_id: str,
        user_id: str,
        project_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve specific memory by ID.

        Delegates to MemoryRetriever micro-component.

        Args:
            memory_id: Memory identifier
            user_id: User identifier
            project_id: Project identifier

        Returns:
            Memory document dict or None if not found
        """
        return await self.memory_retriever.get_memory(
            memory_id=memory_id,
            user_id=user_id,
            project_id=project_id
        )

    async def delete_memory(
        self,
        memory_id: str,
        user_id: str,
        project_id: str
    ) -> bool:
        """
        Delete memory from ChromaDB.

        Delegates to MemoryRetriever micro-component.

        Args:
            memory_id: Memory identifier
            user_id: User identifier
            project_id: Project identifier

        Returns:
            True if deleted, False if not found
        """
        return await self.memory_retriever.delete_memory(
            memory_id=memory_id,
            user_id=user_id,
            project_id=project_id
        )

    async def count_memories(
        self,
        user_id: str,
        project_id: str
    ) -> int:
        """
        Count memories in user/project collection.

        Delegates to MemoryRetriever micro-component.

        Args:
            user_id: User identifier
            project_id: Project identifier

        Returns:
            Number of memories
        """
        return await self.memory_retriever.count_memories(
            user_id=user_id,
            project_id=project_id
        )

    async def store_mental_note_vector(
        self,
        mental_note_id: int,
        mental_note_data: Dict[str, Any],
        user_id: str,
        project_id: str
    ) -> Tuple[str, List[float]]:
        """
        Generate embedding and store mental note in ChromaDB.

        Delegates to NoteStorer micro-component.

        Args:
            mental_note_id: Database ID of mental note
            mental_note_data: Complete mental note data (raw_data dict)
            user_id: User identifier for collection isolation
            project_id: Project identifier for collection isolation

        Returns:
            Tuple of (note_id, embedding_vector)

        Raises:
            ValueError: If content is missing or empty
            ProviderError: If embedding generation fails
        """
        return await self.note_storer.store_mental_note_vector(
            mental_note_id=mental_note_id,
            mental_note_data=mental_note_data,
            user_id=user_id,
            project_id=project_id
        )

    async def search_mental_notes(
        self,
        query: str,
        user_id: str,
        project_id: str,
        limit: int = 10,
        session_id: Optional[str] = None,
        note_type: Optional[str] = None,
        min_similarity: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Semantic search for mental notes.

        Filters by document_type='mental_note' and optionally by session_id or note_type.
        Delegates to NoteSearcher micro-component.

        Args:
            query: Search query text
            user_id: User identifier for collection isolation
            project_id: Project identifier for collection isolation
            limit: Maximum number of results
            session_id: Optional filter by session ID
            note_type: Optional filter by note type (observation, decision, etc.)
            min_similarity: Minimum similarity threshold (0.0 to 1.0)

        Returns:
            List of search results with similarity scores
        """
        return await self.note_searcher.search_mental_notes(
            query=query,
            user_id=user_id,
            project_id=project_id,
            limit=limit,
            session_id=session_id,
            note_type=note_type,
            min_similarity=min_similarity
        )

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
        Generate embeddings and store Gemini memory units in separate ChromaDB collection.

        Uses conversations_{hash(user_id)} collection instead of semantix_{hash}.
        Embeds ONLY Gemini-enriched memory units (not raw conversation).
        Delegates to ConversationStorer micro-component.

        Args:
            conversation_db_id: Database ID of conversation
            conversation_data: Complete conversation data (for metadata only)
            user_id: User identifier for collection isolation
            session_id: Optional session identifier for grouping conversations
            gemini_analysis: List of Gemini-enriched memory units to embed

        Returns:
            Tuple of (list of conversation_ids, list of embedding_vectors)

        Raises:
            ValueError: If no Gemini analysis provided
            ProviderError: If embedding generation fails
        """
        return await self.conversation_storer.store_conversation_vector(
            conversation_db_id=conversation_db_id,
            conversation_data=conversation_data,
            user_id=user_id,
            project_id=project_id,
            session_id=session_id,
            gemini_analysis=gemini_analysis
        )

    async def search_similar_conversations(
        self,
        query: str,
        user_id: str,
        project_id: str,
        limit: int = 10,
        where_filter: Optional[Dict[str, Any]] = None,
        min_similarity: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Semantic search for conversations in separate ChromaDB collection.

        Searches conversations_{hash(user_id)} collection (not semantix_{hash}).
        Delegates to ConversationSearcher micro-component.

        Args:
            query: Search query text
            user_id: User identifier for collection isolation
            limit: Maximum number of results
            where_filter: Optional metadata filter (ChromaDB where syntax)
            min_similarity: Minimum similarity threshold (0.0 to 1.0)

        Returns:
            List of search results with similarity scores
        """
        return await self.conversation_searcher.search_similar_conversations(
            query=query,
            user_id=user_id,
            project_id=project_id,
            limit=limit,
            where_filter=where_filter,
            min_similarity=min_similarity
        )
