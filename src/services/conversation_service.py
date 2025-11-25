"""
Conversation service for business logic.

Handles conversation creation, semantic search, and memory synthesis.
Extracted from conversations.py routes following service layer pattern.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from src.database.repositories import ConversationRepository
from src.modules.core import EventBus, Logger
from src.modules.vector_storage import VectorStorageService
from src.modules.SXThalamus.prompts import SXThalamusPromptBuilder


class ConversationService:
    """
    Service for conversation business logic.

    Handles conversation creation, search, and memory synthesis workflows.
    Delegates data access to ConversationRepository.
    """

    def __init__(
        self,
        repository: Optional[ConversationRepository] = None,
        vector_service: Optional[VectorStorageService] = None,
        llm_service: Optional[Any] = None,
        event_bus: Optional[EventBus] = None,
        logger: Optional[Logger] = None
    ):
        """
        Initialize conversation service with dependencies.

        Args:
            repository: Database repository for conversation persistence
            vector_service: Vector storage service for semantic search
            llm_service: LLM service for memory synthesis
            event_bus: Event bus for publishing events
            logger: Logger instance

        Note: Dependencies are optional to allow flexible usage in different contexts.
        """
        self.repository = repository
        self.vector_service = vector_service
        self.llm_service = llm_service
        self.event_bus = event_bus
        self.logger = logger

    async def create_conversation(
        self,
        conversation_id: str,
        model: str,
        conversation_messages: List[Dict[str, Any]],
        user_id: str,
        project_id: str,
        session_id: Optional[str] = None,
    ):
        """
        Create a new conversation with automatic embedding generation.

        Workflow:
        1. Build raw_data structure from conversation data
        2. Store conversation in PostgreSQL for immediate persistence
        3. Emit conversation.stored event for async vector storage

        Args:
            conversation_id: Unique conversation identifier
            model: AI model name (e.g., "gpt-5-1-instant")
            conversation_messages: List of message dicts with role, message_id, text
            user_id: User identifier
            project_id: Project identifier
            session_id: Optional session identifier

        Returns:
            Created conversation model instance
        """
        self.logger.info(f"Creating conversation: {conversation_id}")

        # Build raw_data structure
        raw_data = self._build_raw_data(
            user_id=user_id,
            project_id=project_id,
            conversation_id=conversation_id,
            model=model,
            conversation_messages=conversation_messages,
            session_id=session_id
        )

        # Create conversation in PostgreSQL (synchronous for immediate response with ID)
        conversation = await self.repository.create(
            conversation_id=conversation_id,
            model=model,
            raw_data=raw_data,
            user_id=user_id,
            project_id=project_id,
            session_id=session_id,
        )

        self.logger.info(f"Conversation stored in PostgreSQL with id: {conversation.id}")

        # Emit event for async vector storage (background task via event handler)
        event_data = {
            "conversation_db_id": conversation.id,
            "conversation_id": conversation_id,
            "model": model,
            "raw_data": raw_data,
            "user_id": user_id,
            "project_id": project_id,
            "session_id": session_id,
            "created_at": conversation.created_at,
        }

        # Use publish (not publish_async) to schedule as background task
        self.event_bus.publish("conversation.stored", event_data)

        self.logger.info(
            f"Conversation created with id {conversation.id}, "
            f"vector storage scheduled as background task (separate collection)"
        )

        return conversation

    async def search_conversations(
        self,
        query: str,
        user_id: str,
        limit: int = 10,
        min_similarity: float = 0.0,
        model: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search for conversations.

        Searches the conversations_{hash} ChromaDB collection using vector embeddings
        to find similar conversations based on semantic similarity.

        Args:
            query: Search query string
            user_id: User identifier for scoping search
            limit: Maximum number of results (default: 10)
            min_similarity: Minimum similarity threshold 0.0-1.0 (default: 0.0)
            model: Optional filter by AI model
            session_id: Optional filter by session

        Returns:
            List of raw search results with metadata, distance, similarity
        """
        self.logger.info(
            f"Searching conversations for: '{query[:100]}' "
            f"(user: {user_id})"
        )

        # Build filter for model and session_id if provided
        combined_filter = self._build_filter(model=model, session_id=session_id)

        # Search conversations using separate collection (user-scoped only)
        results = await self.vector_service.search_similar_conversations(
            query=query,
            user_id=user_id,
            limit=limit,
            where_filter=combined_filter,
            min_similarity=min_similarity
        )

        self.logger.info(f"Found {len(results)} matching conversations")
        return results

    async def fetch_synthesized_memory(
        self,
        query: str,
        user_id: str,
        limit: int = 10,
        min_similarity: float = 0.0,
        model: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> str:
        """
        Fetch synthesized memory from conversation search results.

        Workflow:
        1. Perform semantic search (same as search_conversations)
        2. Handle empty results case
        3. Build synthesis prompt using SXThalamusPromptBuilder
        4. Send to LLM (Gemini) for synthesis
        5. Return synthesized natural language memory

        Args:
            query: Search query string
            user_id: User identifier
            limit: Maximum results (default: 10)
            min_similarity: Minimum similarity threshold (default: 0.0)
            model: Optional filter by AI model
            session_id: Optional filter by session

        Returns:
            Synthesized memory as natural language string
        """
        self.logger.info(
            f"Fetching memory for: '{query[:100]}' "
            f"(user: {user_id})"
        )

        # Build filter for model and session_id if provided
        combined_filter = self._build_filter(model=model, session_id=session_id)

        # Search conversations
        results = await self.vector_service.search_similar_conversations(
            query=query,
            user_id=user_id,
            limit=limit,
            where_filter=combined_filter,
            min_similarity=min_similarity
        )

        self.logger.info(f"Found {len(results)} search results for memory synthesis")

        # Handle empty results
        if not results:
            self.logger.info("No search results found, returning empty memory")
            return "No relevant memories found."

        # Build prompt with search results
        prompt_builder = SXThalamusPromptBuilder()
        prompt = prompt_builder.build_memory_synthesis_prompt(results, query=query)

        self.logger.info(f"Built memory synthesis prompt (length: {len(prompt)})")

        # Call Gemini via centralized LLM service
        synthesized_memory = await self.llm_service.generate_content(
            prompt=prompt,
            user_id=user_id,
            worker_type="memory_synthesizer"
        )

        self.logger.info(
            f"Gemini synthesis completed (length: {len(synthesized_memory)})",
            extra={"preview": synthesized_memory[:200]}
        )

        return synthesized_memory

    def _build_filter(
        self,
        model: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build filter dictionary for conversation search.

        Extracts duplicate filter building logic from search endpoints.

        Args:
            model: Optional AI model filter
            session_id: Optional session filter

        Returns:
            Filter dictionary for ChromaDB where clause
        """
        combined_filter = {}
        if model:
            combined_filter["model"] = model
        if session_id:
            combined_filter["session_id"] = session_id
        return combined_filter

    def _build_raw_data(
        self,
        user_id: str,
        project_id: str,
        conversation_id: str,
        model: str,
        conversation_messages: List[Dict[str, Any]],
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build raw_data structure for conversation storage.

        Args:
            user_id: User identifier
            project_id: Project identifier
            conversation_id: Conversation identifier
            model: AI model name
            conversation_messages: List of message dicts
            session_id: Optional session identifier

        Returns:
            raw_data dictionary with all conversation data
        """
        return {
            "user_id": user_id,
            "project_id": project_id,
            "conversation_id": conversation_id,
            "model": model,
            "conversation": conversation_messages,
            "session_id": session_id,
            "created_at": datetime.utcnow().isoformat()
        }
