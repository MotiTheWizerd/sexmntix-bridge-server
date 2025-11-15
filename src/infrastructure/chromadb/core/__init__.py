"""
ChromaDB Client Core Modules

Provides single-responsibility components for ChromaDB client functionality:
- config: Configuration and settings
- naming_strategy: Collection naming logic
- storage_manager: Storage path and directory management

Note: CollectionManager has been moved to src.infrastructure.chromadb.collection
"""

from .config import ChromaDBConfig
from .naming_strategy import create_collection_name
from .storage_manager import StoragePathManager

__all__ = [
    "ChromaDBConfig",
    "create_collection_name",
    "StoragePathManager",
]
