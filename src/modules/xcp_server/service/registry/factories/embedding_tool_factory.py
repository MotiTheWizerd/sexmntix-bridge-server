"""
Embedding Tool Factory - Creates tools that depend on EmbeddingService
"""
from typing import List
from src.modules.core import EventBus, Logger
from src.modules.embeddings import EmbeddingService
from src.modules.xcp_server.tools import (
    BaseTool,
    SemanticSearchTool,
    EmbeddingTool
)
from .base_factory import BaseToolFactory


class EmbeddingToolFactory(BaseToolFactory):
    """
    Factory for creating tools that require EmbeddingService.

    This factory creates:
    - SemanticSearchTool: Search memories using semantic similarity
    - EmbeddingTool: Generate embeddings for text
    """

    def create_tools(
        self,
        event_bus: EventBus,
        logger: Logger,
        embedding_service: EmbeddingService
    ) -> List[BaseTool]:
        """
        Create embedding-dependent tools.

        Args:
            event_bus: Event bus for publishing events
            logger: Logger instance
            embedding_service: Service for generating embeddings

        Returns:
            List of embedding-dependent tools
        """
        self._validate_dependency(event_bus, 'event_bus')
        self._validate_dependency(logger, 'logger')
        self._validate_dependency(embedding_service, 'embedding_service')

        tools = []

        # Create Semantic Search Tool
        semantic_search_tool = self._create_semantic_search_tool(
            event_bus=event_bus,
            logger=logger,
            embedding_service=embedding_service
        )
        tools.append(semantic_search_tool)

        # Create Embedding Tool
        embedding_tool = self._create_embedding_tool(
            event_bus=event_bus,
            logger=logger,
            embedding_service=embedding_service
        )
        tools.append(embedding_tool)

        logger.debug(f"EmbeddingToolFactory created {len(tools)} tools")
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
