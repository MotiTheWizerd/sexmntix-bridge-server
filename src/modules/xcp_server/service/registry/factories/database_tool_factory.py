"""
Database Tool Factory - Creates tools that depend on database sessions
"""
from typing import List
from src.modules.core import EventBus, Logger
from src.modules.xcp_server.tools import (
    BaseTool,
    StoreMemoryTool,
    StoreMentalNoteTool,
    QueryMentalNotesTool,
    SearchMemoryByDateTool
)
from .base_factory import BaseToolFactory


class DatabaseToolFactory(BaseToolFactory):
    """
    Factory for creating tools that require database session factory.

    This factory creates:
    - StoreMemoryTool: Store memory logs in the database
    - StoreMentalNoteTool: Store mental notes in the database
    - QueryMentalNotesTool: Query mental notes from the database
    """

    def create_tools(
        self,
        event_bus: EventBus,
        logger: Logger,
        db_session_factory
    ) -> List[BaseTool]:
        """
        Create database-dependent tools.

        Args:
            event_bus: Event bus for publishing events
            logger: Logger instance
            db_session_factory: Factory for creating database sessions

        Returns:
            List of database-dependent tools
        """
        self._validate_dependency(event_bus, 'event_bus')
        self._validate_dependency(logger, 'logger')
        self._validate_dependency(db_session_factory, 'db_session_factory')

        tools = []

        # Create Store Memory Tool
        store_memory_tool = self._create_store_memory_tool(
            event_bus=event_bus,
            logger=logger,
            db_session_factory=db_session_factory
        )
        tools.append(store_memory_tool)

        # Create Store Mental Note Tool
        store_mental_note_tool = self._create_store_mental_note_tool(
            event_bus=event_bus,
            logger=logger,
            db_session_factory=db_session_factory
        )
        tools.append(store_mental_note_tool)

        # Create Query Mental Notes Tool
        query_mental_notes_tool = self._create_query_mental_notes_tool(
            event_bus=event_bus,
            logger=logger,
            db_session_factory=db_session_factory
        )
        tools.append(query_mental_notes_tool)

        # Create Search Memory By Date Tool
        search_memory_by_date_tool = self._create_search_memory_by_date_tool(
            event_bus=event_bus,
            logger=logger
        )
        tools.append(search_memory_by_date_tool)

        logger.debug(f"DatabaseToolFactory created {len(tools)} tools")
        return tools

    @staticmethod
    def _create_store_memory_tool(
        event_bus: EventBus,
        logger: Logger,
        db_session_factory
    ) -> StoreMemoryTool:
        """Create StoreMemoryTool with dependencies

        Note: StoreMemoryTool now uses HTTP API instead of direct database access,
        so db_session_factory is not passed to the tool.
        """
        return StoreMemoryTool(
            event_bus=event_bus,
            logger=logger
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

    @staticmethod
    def _create_search_memory_by_date_tool(
        event_bus: EventBus,
        logger: Logger
    ) -> SearchMemoryByDateTool:
        """
        Create SearchMemoryByDateTool with dependencies

        Note: This tool is a dumb HTTP pipeline that forwards requests to the backend API.
        No database session factory needed.
        """
        return SearchMemoryByDateTool(
            event_bus=event_bus,
            logger=logger
        )
