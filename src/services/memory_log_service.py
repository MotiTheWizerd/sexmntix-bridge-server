"""
Memory log business logic service.

Handles memory log operations including creation, search, and date-based filtering.
Orchestrates interactions between repository, vector storage, and event bus.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from src.database.repositories.memory_log_repository import MemoryLogRepository
from src.modules.core import EventBus, Logger
from src.modules.vector_storage import VectorStorageService
from src.utils.date_range_calculator import DateRangeCalculator


class MemoryLogService:
    """Service layer for memory log operations."""

    def __init__(
        self,
        repository: MemoryLogRepository,
        vector_service: VectorStorageService,
        event_bus: EventBus,
        logger: Logger
    ):
        """
        Initialize memory log service.

        Args:
            repository: Database repository for memory logs
            vector_service: Vector storage service for semantic search
            event_bus: Event bus for async operations
            logger: Logger instance
        """
        self.repository = repository
        self.vector_service = vector_service
        self.event_bus = event_bus
        self.logger = logger

    def unwrap_request_body(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """
        Unwrap request body from various formats (MCP-wrapped or direct).

        Args:
            body: Raw request body

        Returns:
            Unwrapped data dictionary

        Examples:
            >>> # Already unwrapped
            >>> unwrap_request_body({"task": "foo", "agent": "bar", "user_id": "123"})
            {"task": "foo", "agent": "bar", "user_id": "123"}

            >>> # MCP-wrapped
            >>> unwrap_request_body({"memory_log": {"task": "foo", ...}})
            {"task": "foo", ...}
        """
        self.logger.debug(f"[SERVICE_UNWRAP] Raw request body keys: {list(body.keys())}")

        # Check if already in correct format (has task, agent, user_id at top level)
        if "task" in body and "agent" in body and "user_id" in body:
            self.logger.debug("[SERVICE_UNWRAP] Already in correct format")
            return body

        # MCP-wrapped, extract inner structure
        elif "memory_log" in body and isinstance(body["memory_log"], dict):
            self.logger.debug("[SERVICE_UNWRAP] Unwrapped MCP wrapper")
            return body["memory_log"]

        # Unknown format, try as-is
        else:
            self.logger.debug("[SERVICE_UNWRAP] Unknown format, using body as-is")
            return body

    async def create_memory_log(
        self,
        task: str,
        agent: str,
        session_id: str,
        memory_log: Dict[str, Any],
        user_id: str,
        project_id: str
    ) -> Any:
        """
        Create a new memory log with event-driven vector storage.

        Workflow:
        1. Store in PostgreSQL (immediate persistence)
        2. Emit event for async ChromaDB vector storage

        Args:
            task: Task name (kebab-case)
            agent: Agent identifier
            session_id: Session identifier
            memory_log: Memory log data dictionary
            user_id: User identifier
            project_id: Project identifier

        Returns:
            Created memory log model
        """
        self.logger.info(f"Creating memory log for task: {task}")

        # Create memory log in PostgreSQL
        memory_log_model = await self.repository.create(
            task=task,
            agent=agent,
            session_id=session_id,
            memory_log=memory_log,
            user_id=str(user_id),
            project_id=project_id,
        )

        self.logger.info(f"Memory log stored in PostgreSQL with id: {memory_log_model.id}")

        # Emit event for async vector storage
        event_data = {
            "memory_log_id": memory_log_model.id,
            "task": task,
            "agent": agent,
            "session_id": session_id,
            "memory_log": memory_log,
            "user_id": str(user_id),
            "project_id": project_id,
        }

        self.event_bus.publish("memory_log.stored", event_data)

        self.logger.info(
            f"Memory log created with id {memory_log_model.id}, "
            f"vector storage scheduled as background task"
        )

        return memory_log_model

    async def search_memory_logs(
        self,
        query: str,
        user_id: str,
        project_id: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        tag: Optional[str] = None,
        min_similarity: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Semantic search for memory logs.

        Args:
            query: Search query
            user_id: User identifier
            project_id: Project identifier
            limit: Maximum number of results
            filters: Optional metadata filters
            tag: Optional tag filter
            min_similarity: Minimum similarity threshold

        Returns:
            List of search results with id, document, metadata, distance, similarity
        """
        self.logger.info(
            f"Searching memory logs for: '{query[:100]}' "
            f"(user: {user_id}, project: {project_id})"
        )

        # Build combined filter with tag if provided
        combined_filter = filters or {}
        if tag:
            # Add tag filter - tags are stored in metadata as:
            # 1. tag_0, tag_1, tag_2, tag_3, tag_4 (individual fields)
            # 2. tags (comma-separated string)
            tag_filter = {
                "$or": [
                    {"tag_0": tag},
                    {"tag_1": tag},
                    {"tag_2": tag},
                    {"tag_3": tag},
                    {"tag_4": tag},
                    {"tags": {"$contains": tag}}
                ]
            }
            # Combine with existing filters using $and
            if combined_filter:
                combined_filter = {"$and": [combined_filter, tag_filter]}
            else:
                combined_filter = tag_filter

        results = await self.vector_service.search_similar_memories(
            query=query,
            user_id=user_id,
            project_id=project_id,
            limit=limit,
            where_filter=combined_filter,
            min_similarity=min_similarity
        )

        self.logger.info(f"Found {len(results)} matching memories")
        return results

    async def search_by_date(
        self,
        query: str,
        user_id: str,
        project_id: str,
        limit: int = 10,
        time_period: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Search memory logs with date filtering.

        Args:
            query: Search query
            user_id: User identifier
            project_id: Project identifier
            limit: Maximum number of results
            time_period: Shortcut like "recent", "last-week", "last-month", "archived"
            start_date: Explicit start date
            end_date: Explicit end date

        Returns:
            List of search results
        """
        self.logger.info(
            f"Searching memory logs by date for: '{query[:100]}' "
            f"(user: {user_id}, project: {project_id})"
        )

        # Calculate date range using utility
        start_date, end_date = DateRangeCalculator.calculate(
            time_period=time_period,
            start_date=start_date,
            end_date=end_date
        )

        # Build ChromaDB filter for date range
        where_filter = {}
        if start_date:
            where_filter["date"] = {"$gte": start_date.isoformat()}
        if end_date and start_date:
            where_filter["date"] = {
                "$gte": start_date.isoformat(),
                "$lte": end_date.isoformat()
            }
        elif end_date:
            where_filter["date"] = {"$lte": end_date.isoformat()}

        # Perform semantic search with date filter
        results = await self.vector_service.search_similar_memories(
            query=query,
            user_id=user_id,
            project_id=project_id,
            limit=limit,
            where_filter=where_filter if where_filter else None,
            min_similarity=0.0
        )

        self.logger.info(f"Found {len(results)} matching memories")
        return results
