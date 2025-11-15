"""
Semantic Search Tool Package

Provides semantic search capabilities for memory logs using vector similarity.

This package is organized into the following components:
- tool: Main tool implementation (SemanticSearchTool)
- config: Tool definition and parameter schemas
- validators: Argument validation logic
- formatters: Result formatting utilities

Usage:
    from src.modules.xcp_server.tools.semantic_search import SemanticSearchTool

    tool = SemanticSearchTool(event_bus, logger, embedding_service)
"""

from .tool import SemanticSearchTool
from .config import SemanticSearchConfig
from .validators import SearchArgumentValidator
from .formatters import SearchResultFormatter

__all__ = [
    "SemanticSearchTool",
    "SemanticSearchConfig",
    "SearchArgumentValidator",
    "SearchResultFormatter"
]
