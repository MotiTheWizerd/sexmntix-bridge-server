"""
Tool Factory - Creates and configures MCP tools with dependencies

This module provides the main ToolFactory class that orchestrates the creation
of all MCP tools by delegating to specialized factory classes.
"""
from typing import List
from src.modules.core import EventBus, Logger
from src.modules.embeddings import EmbeddingService
from src.modules.xcp_server.tools import BaseTool
from .factories import EmbeddingToolFactory, DatabaseToolFactory


class ToolFactory:
    """
    Factory for creating MCP tools with proper dependency injection.

    This factory orchestrates the creation of all tools by delegating to
    specialized factories that handle different categories of tools:
    - EmbeddingToolFactory: Tools requiring EmbeddingService
    - DatabaseToolFactory: Tools requiring database sessions

    This approach improves modularity and maintainability by grouping
    tools with similar dependencies together.
    """

    def __init__(self):
        """Initialize the tool factory with specialized factories"""
        self.embedding_factory = EmbeddingToolFactory()
        self.database_factory = DatabaseToolFactory()

    def create_tools(
        self,
        event_bus: EventBus,
        logger: Logger,
        embedding_service: EmbeddingService,
        db_session_factory
    ) -> List[BaseTool]:
        """
        Create all MCP tools with their dependencies.

        This method aggregates tools from specialized factories to provide
        a complete list of all available MCP tools.

        Args:
            event_bus: Event bus for publishing events
            logger: Logger instance
            embedding_service: Embedding generation service
            db_session_factory: Factory for creating database sessions

        Returns:
            List of initialized tools from all factories
        """
        tools = []

        # Create embedding-dependent tools
        embedding_tools = self.embedding_factory.create_tools(
            event_bus=event_bus,
            logger=logger,
            embedding_service=embedding_service
        )
        tools.extend(embedding_tools)

        # Create database-dependent tools
        database_tools = self.database_factory.create_tools(
            event_bus=event_bus,
            logger=logger,
            db_session_factory=db_session_factory
        )
        tools.extend(database_tools)

        logger.info(f"Created {len(tools)} MCP tools")
        return tools
