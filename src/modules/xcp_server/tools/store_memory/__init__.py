"""
Store Memory Tool - MCP Tool for storing new memory logs

Enables AI assistants to store new memories with automatic vector
embedding generation for semantic search.

Public API for the store_memory tool package.
"""

from src.modules.xcp_server.tools.store_memory.tool import StoreMemoryTool
from src.modules.xcp_server.tools.store_memory.config import StoreMemoryConfig

__all__ = [
    "StoreMemoryTool",
    "StoreMemoryConfig",
]
