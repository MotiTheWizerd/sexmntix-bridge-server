"""
Vector Storage Service

Single Responsibility: Orchestrate vector storage operations by delegating
to specialized components.

This service acts as a facade/coordinator, composing:
- MemoryTextExtractor: Extract searchable text from data
- MemoryStorageHandler: Handle vector storage operations
- SimilaritySearchHandler: Handle semantic search operations
"""

from typing import List, Dict, Any, Optional
from src.modules.core import EventBus, Logger
from src.modules.embeddings import EmbeddingService
from src.infrastructure.chromadb.repository import VectorRepository

from src.modules.vector_storage.text_extraction import MemoryTextExtractor
from src.modules.vector_storage.storage import MemoryStorageHandler
from src.modules.vector_storage.search import SimilaritySearchHandler, SimilarityFilter
from src.modules.vector_storage.config import VectorStorageConfig, DEFAULT_CONFIG
from src.modules.vector_storage.models import MemorySearchRequest, MemorySearchResult


class VectorStorageService:
    """
    Service for managing vector embeddings and semantic search.

    Orchestrates specialized components:
    - MemoryTextExtractor: Text extraction from memory data
    - MemoryStorageHandler: Vector storage operations
    - SimilaritySearchHandler: Semantic search operations
    - SimilarityFilter: Result filtering

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
        Initialize vector storage service with component composition.

        Args:
            event_bus: Event bus for publishing domain events
            logger: Logger instance
            embedding_service: Service for generating embeddings
            vector_repository: Repository for ChromaDB operations
        """
        self.event_bus = event_bus
        self.logger = logger

        # Initialize specialized components
        self.text_extractor = MemoryTextExtractor(logger)

        self.storage_handler = MemoryStorageHandler(
            event_bus=event_bus,
            logger=logger,
            embedding_service=embedding_service,
            vector_repository=vector_repository
        )

        self.similarity_filter = SimilarityFilter()

        self.search_handler = SimilaritySearchHandler(
            event_bus=event_bus,
            logger=logger,
            embedding_service=embedding_service,
            vector_repository=vector_repository,
            similarity_filter=self.similarity_filter
        )

        self.logger.info("VectorStorageService initialized with modular components")

    async def store_memory_vector(
        self,
        memory_log_id: int,
        memory_data: Dict[str, Any],
        user_id: str,
        project_id: str,
        text_override: Optional[str] = None
    ) -> tuple[str, List[float]]:
        """
        Generate embedding and store in ChromaDB.

        Delegates to specialized components:
        1. MemoryTextExtractor: Extract searchable text
        2. MemoryStorageHandler: Store vector

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
        # Extract searchable text using TextExtractor
        if text_override:
            searchable_text = text_override
        else:
            searchable_text = self.text_extractor.extract_with_fallback(
                memory_data=memory_data,
                memory_log_id=memory_log_id
            )

        # Store vector using StorageHandler
        return await self.storage_handler.store_memory_vector(
            memory_log_id=memory_log_id,
            searchable_text=searchable_text,
            memory_data=memory_data,
            user_id=user_id,
            project_id=project_id
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
        Delegates to SimilaritySearchHandler.

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

        Example:
            results = await service.search_similar_memories(
                query="authentication bug fix",
                user_id="user123",
                project_id="project456",
                limit=5,
                min_similarity=0.5,
                enable_temporal_decay=True,
                half_life_days=30
            )
        """
        # Ensure we only search memory logs, not mental notes
        combined_filter = where_filter.copy() if where_filter else {}
        combined_filter["document_type"] = "memory_log"

        return await self.search_handler.search_similar_memories(
            query=query,
            user_id=user_id,
            project_id=project_id,
            limit=limit,
            where_filter=combined_filter,
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

        Delegates to MemoryStorageHandler.

        Args:
            memory_id: Memory identifier
            user_id: User identifier
            project_id: Project identifier

        Returns:
            Memory document dict or None if not found
        """
        return await self.storage_handler.get_memory(
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

        Delegates to MemoryStorageHandler.

        Args:
            memory_id: Memory identifier
            user_id: User identifier
            project_id: Project identifier

        Returns:
            True if deleted, False if not found
        """
        return await self.storage_handler.delete_memory(
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

        Delegates to MemoryStorageHandler.

        Args:
            user_id: User identifier
            project_id: Project identifier

        Returns:
            Number of memories
        """
        return await self.storage_handler.count_memories(
            user_id=user_id,
            project_id=project_id
        )

    async def store_mental_note_vector(
        self,
        mental_note_id: int,
        mental_note_data: Dict[str, Any],
        user_id: str,
        project_id: str
    ) -> tuple[str, List[float]]:
        """
        Generate embedding and store mental note in ChromaDB.

        Delegates to MemoryStorageHandler for mental note vector storage.

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
        return await self.storage_handler.store_mental_note_vector(
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

        Example:
            results = await service.search_mental_notes(
                query="bug fix discussion",
                user_id="00000000-0000-0000-0000-000000000001",
                project_id="default",
                session_id="session_123",
                note_type="decision",
                limit=10,
                min_similarity=0.5
            )
        """
        # Build where filter for mental notes
        where_filter = {"document_type": "mental_note"}

        if session_id:
            where_filter["session_id"] = session_id

        if note_type:
            where_filter["note_type"] = note_type

        # Use the same search handler as memory logs
        return await self.search_handler.search_similar_memories(
            query=query,
            user_id=user_id,
            project_id=project_id,
            limit=limit,
            where_filter=where_filter,
            min_similarity=min_similarity,
            enable_temporal_decay=False,  # Mental notes don't use temporal decay
            half_life_days=30.0
        )

    def _build_embedding_text_from_memory_unit(self, memory_unit: Dict[str, Any]) -> str:
        """
        Build natural language embedding text from Gemini memory unit.
        
        Combines: topic + summary + key_points + tags + related_topics + reflection
        into a single semantic paragraph for clean embedding.
        
        Args:
            memory_unit: Gemini-enriched memory object
            
        Returns:
            Natural language text ready for embedding
        """
        parts = []
        
        # Topic (title/subject)
        if topic := memory_unit.get("topic"):
            parts.append(topic + ".")
        
        # Summary (main content)
        if summary := memory_unit.get("summary"):
            parts.append(summary)
        
        # Key points (as natural list)
        if key_points := memory_unit.get("key_points"):
            if isinstance(key_points, list):
                parts.append(" ".join(key_points))
        
        # Tags (semantic labels)
        if tags := memory_unit.get("tags"):
            if isinstance(tags, list):
                parts.append(f"Tags: {', '.join(tags)}.")
        
        # Related topics (connections)
        if related_topics := memory_unit.get("related_topics"):
            if isinstance(related_topics, list):
                parts.append(f"Related topics: {', '.join(related_topics)}.")
        
        # Reflection (meta-cognitive insight)
        if reflection := memory_unit.get("reflection"):
            parts.append(f"Reflection: {reflection}")
        
        # Join into natural paragraph with spaces
        return " ".join(parts)

    async def store_conversation_vector(
        self,
        conversation_db_id: int,
        conversation_data: Dict[str, Any],
        user_id: str,
        gemini_analysis: List[Dict[str, Any]] = None
    ) -> tuple[List[str], List[List[float]]]:
        """
        Generate embeddings and store Gemini memory units in separate ChromaDB collection.

        Uses conversations_{hash(user_id)} collection instead of semantix_{hash}.
        Embeds ONLY Gemini-enriched memory units (not raw conversation).
        Storage structure: user_id/conversations/{conversation_id}/

        Args:
            conversation_db_id: Database ID of conversation
            conversation_data: Complete conversation data (for metadata only)
            user_id: User identifier for collection isolation
            gemini_analysis: List of Gemini-enriched memory units to embed

        Returns:
            Tuple of (list of conversation_ids, list of embedding_vectors)

        Raises:
            ValueError: If no Gemini analysis provided
            ProviderError: If embedding generation fails
        """
        from src.infrastructure.chromadb.operations.conversation import create_conversation

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

        # Get ChromaDB client
        chromadb_client = self.storage_handler.vector_repository.client

        conversation_ids = []
        embeddings = []

        # Process each memory unit separately
        for idx, memory_unit in enumerate(gemini_analysis):
            # Build natural language text for embedding
            embedding_text = self._build_embedding_text_from_memory_unit(memory_unit)

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
            embedding_result = await self.storage_handler.embedding_service.generate_embedding(
                embedding_text
            )
            embedding = embedding_result.embedding

            self.logger.info(
                f"[CONVERSATION_STORAGE] Embedding generated for memory unit {idx} "
                f"(dimensions: {len(embedding)}, cached: {embedding_result.cached})"
            )

            # Store in ChromaDB with memory unit JSON as document
            conversation_id = await create_conversation(
                client=chromadb_client,
                conversation_db_id=conversation_db_id,
                embedding=embedding,
                conversation_data=memory_unit,  # Store memory unit, not full conversation
                user_id=user_id,
                memory_index=idx
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

        return conversation_ids, embeddings

    async def search_similar_conversations(
        self,
        query: str,
        user_id: str,
        limit: int = 10,
        where_filter: Optional[Dict[str, Any]] = None,
        min_similarity: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Semantic search for conversations in separate ChromaDB collection.

        Searches conversations_{hash(user_id)} collection (not semantix_{hash}).
        Storage structure: user_id/conversations/{conversation_id}/

        Args:
            query: Search query text
            user_id: User identifier for collection isolation
            limit: Maximum number of results
            where_filter: Optional metadata filter (ChromaDB where syntax)
            min_similarity: Minimum similarity threshold (0.0 to 1.0)

        Returns:
            List of search results with similarity scores

        Example:
            results = await service.search_similar_conversations(
                query="authentication discussion",
                user_id="00000000-0000-0000-0000-000000000001",
                limit=5,
                where_filter={"model": "gpt-5-1-instant"},
                min_similarity=0.5
            )
        """
        from src.infrastructure.chromadb.operations.conversation.crud import search_conversations

        self.logger.info(
            f"[CONVERSATION_SEARCH] Searching conversations for query: '{query[:100]}'"
        )

        # Generate embedding for query
        embedding_result = await self.storage_handler.embedding_service.generate_embedding(query)
        query_embedding = embedding_result.embedding

        # Get ChromaDB client
        chromadb_client = self.storage_handler.vector_repository.client

        # Perform semantic search using conversation-specific search function
        results = await search_conversations(
            client=chromadb_client,
            query_embedding=query_embedding,
            user_id=user_id,
            limit=limit,
            where_filter=where_filter,
            min_similarity=min_similarity
        )

        self.logger.info(
            f"[CONVERSATION_SEARCH] Found {len(results)} matching conversations"
        )

        return results
