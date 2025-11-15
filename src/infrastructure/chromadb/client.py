"""
ChromaDB Client Wrapper

Provides a persistent ChromaDB client with configuration and collection management.
Orchestrates core modules: naming strategy, storage management, and collection operations.

Based on TypeScript architecture from 03-chromadb-storage.md.

Storage Path: ./data/chromadb/{user_id}/{project_id}
Collection Naming: {prefix}_{hash16} where hash16 is SHA256(user_id:project_id)[:16]
"""

from typing import Optional
import chromadb
from chromadb.config import Settings
from chromadb import Collection
from src.modules.core.telemetry.logger import get_logger
from .core.config import ChromaDBConfig, DEFAULT_CONFIG
from .core.storage_manager import StoragePathManager
from .collection import CollectionManager


class ChromaDBClient:
    """
    Wrapper for ChromaDB PersistentClient with collection caching and multi-tenant support.

    This class acts as a facade that orchestrates:
    - StoragePathManager: Manages storage paths and directories
    - CollectionManager: Handles collection CRUD operations
    - ChromaDBConfig: Configuration management

    Features:
    - Persistent local storage with nested user_id/project_id directories
    - Multi-user/project isolation via collection naming and storage paths
    - Collection caching for performance
    - Automatic collection creation
    - Health monitoring via heartbeat
    """

    def __init__(
        self,
        storage_path: str = "./data/chromadb",
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        config: Optional[ChromaDBConfig] = None
    ):
        """
        Initialize ChromaDB persistent client.

        Args:
            storage_path: Base path to ChromaDB storage directory
            user_id: Optional user ID for nested directory structure
            project_id: Optional project ID for nested directory structure
            config: Optional ChromaDB configuration (default: DEFAULT_CONFIG)
        """
        self.base_storage_path = storage_path
        self.default_user_id = user_id
        self.default_project_id = project_id
        self.config = config or DEFAULT_CONFIG
        self.logger = get_logger(__name__)

        # Initialize storage path manager
        self.storage_manager = StoragePathManager(storage_path)

        # Get or create the storage path
        self.storage_path = self.storage_manager.ensure_path_exists(user_id, project_id)

        # Initialize persistent client
        self.client = chromadb.PersistentClient(
            path=self.storage_path,
            settings=Settings(
                anonymized_telemetry=self.config.anonymized_telemetry,
                allow_reset=self.config.allow_reset
            )
        )

        # Initialize collection manager
        self.collection_manager = CollectionManager(self.client, self.config)

    def get_collection(
        self,
        user_id: str,
        project_id: str,
        collection_prefix: Optional[str] = None
    ) -> Collection:
        """
        Get or create a collection with user/project isolation.

        Collection naming uses hash to meet ChromaDB 63-character limit.
        Pattern: {prefix}_{hash16}
        Hash is based on SHA256(user_id:project_id)

        Example: semantix_a1b2c3d4e5f6g7h8

        Args:
            user_id: User identifier for isolation
            project_id: Project identifier for isolation
            collection_prefix: Prefix for collection name (default: config.default_collection_prefix)

        Returns:
            ChromaDB Collection instance
        """
        return self.collection_manager.get_collection(user_id, project_id, collection_prefix)

    def list_collections(self) -> list[str]:
        """
        List all collection names in the database.

        Returns:
            List of collection names
        """
        return self.collection_manager.list_collections()

    def delete_collection(
        self,
        user_id: str,
        project_id: str,
        collection_prefix: Optional[str] = None
    ) -> None:
        """
        Delete a specific collection.

        Args:
            user_id: User identifier
            project_id: Project identifier
            collection_prefix: Prefix for collection name (default: config.default_collection_prefix)
        """
        self.collection_manager.delete_collection(user_id, project_id, collection_prefix)

    def reset(self) -> None:
        """
        Reset the entire ChromaDB instance.
        WARNING: This deletes all collections and data!
        """
        self.logger.warning(
            "[CHROMADB_CLIENT] Resetting entire ChromaDB instance - all data will be deleted!"
        )
        self.client.reset()
        self.collection_manager.clear_cache()

    def heartbeat(self) -> int:
        """
        Check ChromaDB connection health.

        Returns:
            Heartbeat timestamp in nanoseconds
        """
        return self.client.heartbeat()
