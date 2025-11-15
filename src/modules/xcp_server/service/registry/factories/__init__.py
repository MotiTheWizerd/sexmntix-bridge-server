"""
Factory components for tool creation

This package provides specialized factories for creating different categories of tools:
- BaseToolFactory: Abstract base class for all factories
- EmbeddingToolFactory: Creates tools that require EmbeddingService
- DatabaseToolFactory: Creates tools that require database sessions

Usage:
    from src.modules.xcp_server.service.registry.factories import (
        EmbeddingToolFactory,
        DatabaseToolFactory
    )

    embedding_factory = EmbeddingToolFactory()
    embedding_tools = embedding_factory.create_tools(event_bus, logger, embedding_service)

    database_factory = DatabaseToolFactory()
    database_tools = database_factory.create_tools(event_bus, logger, db_session_factory)
"""
from .base_factory import BaseToolFactory
from .embedding_tool_factory import EmbeddingToolFactory
from .database_tool_factory import DatabaseToolFactory

__all__ = [
    'BaseToolFactory',
    'EmbeddingToolFactory',
    'DatabaseToolFactory',
]
