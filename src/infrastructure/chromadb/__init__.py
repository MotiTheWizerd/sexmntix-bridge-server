"""
ChromaDB Infrastructure

Provides ChromaDB client wrapper and vector repository for semantic storage.
"""

from .client import ChromaDBClient
from .repository import VectorRepository
from .core import ChromaDBConfig, create_collection_name, StoragePathManager
from .collection import CollectionManager
from .models import SearchResult
from .utils import (
    generate_memory_id,
    convert_to_timestamp,
    prepare_metadata,
    build_tag_filter,
    sanitize_filter,
)
from .operations import memory, search_operations

__all__ = [
    # Main classes
    "ChromaDBClient",
    "VectorRepository",
    "SearchResult",
    # Core modules for direct usage if needed
    "ChromaDBConfig",
    "create_collection_name",
    "StoragePathManager",
    "CollectionManager",
    # Utilities for direct usage
    "generate_memory_id",
    "convert_to_timestamp",
    "prepare_metadata",
    "build_tag_filter",
    "sanitize_filter",
    # Operations modules for advanced usage
    "memory",
    "search_operations",
]
