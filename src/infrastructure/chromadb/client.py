"""
ChromaDB Client Wrapper

Provides a persistent ChromaDB client with configuration and collection management.
Based on TypeScript architecture from 03-chromadb-storage.md.

Storage Path: ./data/chromadb/{user_id}/{project_id}
Collection Naming: semantix_memories_{user_id}_{project_id}
"""

import os
from pathlib import Path
from typing import Optional
import chromadb
from chromadb.config import Settings
from chromadb import Collection


class ChromaDBClient:
    """
    Wrapper for ChromaDB PersistentClient with collection caching.

    Features:
    - Persistent local storage with nested user_id/project_id directories
    - Multi-user/project isolation via collection naming and storage paths
    - Collection caching for performance
    - Automatic collection creation
    """

    def __init__(self, storage_path: str = "./data/chromadb", user_id: Optional[str] = None, project_id: Optional[str] = None):
        """
        Initialize ChromaDB persistent client.

        Args:
            storage_path: Base path to ChromaDB storage directory
            user_id: Optional user ID for nested directory structure
            project_id: Optional project ID for nested directory structure
        """
        self.base_storage_path = storage_path
        self.default_user_id = user_id
        self.default_project_id = project_id

        # Build storage path with nesting if user_id/project_id provided
        if user_id and project_id:
            self.storage_path = str(Path(storage_path) / user_id / project_id)
        else:
            self.storage_path = storage_path

        self._ensure_storage_path()

        # Initialize persistent client
        self.client = chromadb.PersistentClient(
            path=self.storage_path,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Collection cache for performance
        self._collections: dict[str, Collection] = {}

        # Client cache for different user/project combinations
        self._clients: dict[str, chromadb.PersistentClient] = {}

    def _ensure_storage_path(self):
        """Create storage directory if it doesn't exist."""
        os.makedirs(self.storage_path, exist_ok=True)

    def get_collection(
        self,
        user_id: str,
        project_id: str,
        collection_prefix: str = "semantix_memories"
    ) -> Collection:
        """
        Get or create a collection with user/project isolation.

        Collection naming pattern: {prefix}_{user_id}_{project_id}
        Example: semantix_memories_user123_project456

        Args:
            user_id: User identifier for isolation
            project_id: Project identifier for isolation
            collection_prefix: Prefix for collection name

        Returns:
            ChromaDB Collection instance
        """
        collection_name = f"{collection_prefix}_{user_id}_{project_id}"

        # Return cached collection if available
        if collection_name in self._collections:
            return self._collections[collection_name]

        # Create or get collection
        collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"user_id": user_id, "project_id": project_id}
        )

        # Cache for future use
        self._collections[collection_name] = collection

        return collection

    def list_collections(self) -> list[str]:
        """
        List all collection names in the database.

        Returns:
            List of collection names
        """
        collections = self.client.list_collections()
        return [col.name for col in collections]

    def delete_collection(
        self,
        user_id: str,
        project_id: str,
        collection_prefix: str = "semantix_memories"
    ):
        """
        Delete a specific collection.

        Args:
            user_id: User identifier
            project_id: Project identifier
            collection_prefix: Prefix for collection name
        """
        collection_name = f"{collection_prefix}_{user_id}_{project_id}"

        # Remove from cache
        if collection_name in self._collections:
            del self._collections[collection_name]

        # Delete from ChromaDB
        self.client.delete_collection(collection_name)

    def reset(self):
        """
        Reset the entire ChromaDB instance.
        WARNING: This deletes all collections and data!
        """
        self.client.reset()
        self._collections.clear()

    def heartbeat(self) -> int:
        """
        Check ChromaDB connection health.

        Returns:
            Heartbeat timestamp in nanoseconds
        """
        return self.client.heartbeat()
