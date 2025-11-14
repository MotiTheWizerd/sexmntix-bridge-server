"""
Vector Storage Module

Provides semantic search capabilities through embedding generation and vector storage.
Organized into single-responsibility components:
- text_extraction: Extract searchable text from data structures
- storage: Handle vector storage operations
- search: Semantic search and similarity filtering
- models: Data transfer objects and result models
- utils: Helper utilities (metadata building, query building)
- config: Configuration management
"""

from src.modules.vector_storage.service import VectorStorageService
from src.modules.vector_storage.config import VectorStorageConfig, DEFAULT_CONFIG
from src.modules.vector_storage.models import (
    MemorySearchRequest,
    MemorySearchResult,
    StorageMetrics,
)
from src.modules.vector_storage.utils import MetadataBuilder, QueryBuilder

__all__ = [
    # Main service
    "VectorStorageService",
    # Configuration
    "VectorStorageConfig",
    "DEFAULT_CONFIG",
    # Models and DTOs
    "MemorySearchRequest",
    "MemorySearchResult",
    "StorageMetrics",
    # Utilities
    "MetadataBuilder",
    "QueryBuilder",
]
