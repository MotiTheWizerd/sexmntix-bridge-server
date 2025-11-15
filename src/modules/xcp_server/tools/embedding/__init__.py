"""
Embedding Tool Package

Provides text embedding generation capabilities using configured embedding models.

This package is organized into the following components:
- tool: Main tool implementation (EmbeddingTool)
- config: Tool definition and parameter schemas
- validators: Argument validation logic
- formatters: Result formatting utilities

Usage:
    from src.modules.xcp_server.tools.embedding import EmbeddingTool

    tool = EmbeddingTool(event_bus, logger, embedding_service)
"""

from .tool import EmbeddingTool
from .config import EmbeddingToolConfig
from .validators import EmbeddingArgumentValidator
from .formatters import EmbeddingResultFormatter

__all__ = [
    "EmbeddingTool",
    "EmbeddingToolConfig",
    "EmbeddingArgumentValidator",
    "EmbeddingResultFormatter"
]
