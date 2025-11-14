"""
ChromaDB Client Core Modules

Provides single-responsibility components for ChromaDB client functionality:
- config: Configuration and settings
- naming_strategy: Collection naming logic
- storage_manager: Storage path and directory management
- collection_manager: Collection CRUD operations
"""

from .config import ChromaDBConfig
from .naming_strategy import create_collection_name
from .storage_manager import StoragePathManager
from .collection_manager import CollectionManager

__all__ = [
    "ChromaDBConfig",
    "create_collection_name",
    "StoragePathManager",
    "CollectionManager",
]
