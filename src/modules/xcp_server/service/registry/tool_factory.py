"""Tool Factory - Creates and configures MCP tools with dependencies"""

from typing import List
from src.modules.core import EventBus, Logger
from src.modules.embeddings import EmbeddingService
from src.modules.xcp_server.tools import (
    BaseTool,
    SemanticSearchTool,
    StoreMemoryTool,
    EmbeddingTool,
    StoreMentalNoteTool,
    QueryMentalNotesTool
)


class ToolFactory:
    """Factory for creating MCP tools with proper dependency injection"""

    def create_tools(
        self,
        event_bus: EventBus,
        logger: Logger,
        embedding_service: EmbeddingService,
        db_session_factory
    ) -> List[BaseTool]:
        """Create all MCP tools with their dependencies

        Args:
            event_bus: Event bus for publishing events
            logger: Logger instance
            embedding_service: Embedding generation service
            db_session_factory: Factory for creating database sessions

        Returns:
            List of initialized tools
        """
        tools = []

        # 1. Semantic Search Tool
        semantic_search_tool = self._create_semantic_search_tool(
            event_bus=event_bus,
            logger=logger,
            embedding_service=embedding_service
        )
        tools.append(semantic_search_tool)

        # 2. Store Memory Tool
        store_memory_tool = self._create_store_memory_tool(
            event_bus=event_bus,
            logger=logger,
            db_session_factory=db_session_factory
        )
        tools.append(store_memory_tool)

        # 3. Embedding Tool
        embedding_tool = self._create_embedding_tool(
            event_bus=event_bus,
            logger=logger,
            embedding_service=embedding_service
        )
        tools.append(embedding_tool)

        # 4. Store Mental Note Tool
        store_mental_note_tool = self._create_store_mental_note_tool(
            event_bus=event_bus,
            logger=logger,
            db_session_factory=db_session_factory
        )
        tools.append(store_mental_note_tool)

        # 5. Query Mental Notes Tool
        query_mental_notes_tool = self._create_query_mental_notes_tool(
            event_bus=event_bus,
            logger=logger,
            db_session_factory=db_session_factory
        )
        tools.append(query_mental_notes_tool)

        logger.info(f"Created {len(tools)} MCP tools")
        return tools

    @staticmethod
    def _create_semantic_search_tool(
        event_bus: EventBus,
        logger: Logger,
        embedding_service: EmbeddingService
    ) -> SemanticSearchTool:
        """Create SemanticSearchTool with dependencies"""
        return SemanticSearchTool(
            event_bus=event_bus,
            logger=logger,
            embedding_service=embedding_service
        )

    @staticmethod
    def _create_store_memory_tool(
        event_bus: EventBus,
        logger: Logger,
        db_session_factory
    ) -> StoreMemoryTool:
        """Create StoreMemoryTool with dependencies"""
        return StoreMemoryTool(
            event_bus=event_bus,
            logger=logger,
            db_session_factory=db_session_factory
        )

    @staticmethod
    def _create_embedding_tool(
        event_bus: EventBus,
        logger: Logger,
        embedding_service: EmbeddingService
    ) -> EmbeddingTool:
        """Create EmbeddingTool with dependencies"""
        return EmbeddingTool(
            event_bus=event_bus,
            logger=logger,
            embedding_service=embedding_service
        )

    @staticmethod
    def _create_store_mental_note_tool(
        event_bus: EventBus,
        logger: Logger,
        db_session_factory
    ) -> StoreMentalNoteTool:
        """Create StoreMentalNoteTool with dependencies"""
        return StoreMentalNoteTool(
            event_bus=event_bus,
            logger=logger,
            db_session_factory=db_session_factory
        )

    @staticmethod
    def _create_query_mental_notes_tool(
        event_bus: EventBus,
        logger: Logger,
        db_session_factory
    ) -> QueryMentalNotesTool:
        """Create QueryMentalNotesTool with dependencies"""
        return QueryMentalNotesTool(
            event_bus=event_bus,
            logger=logger,
            db_session_factory=db_session_factory
        )
