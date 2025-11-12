"""
ChromaDB Client Wrapper

Provides a persistent ChromaDB client with configuration and collection management.
Based on TypeScript architecture from 03-chromadb-storage.md.

Storage Path: ./data/chromadb
Collection Naming: semantix_memories_{user_id}_{project_id}
"""

import os
from typing import Optional
import chromadb
from chromadb.config import Settings
from chromadb import Collection


class ChromaDBClient:
    """
    Wrapper for ChromaDB PersistentClient with collection caching.

    Features:
    - Persistent local storage
    - Multi-user/project isolation via collection naming
    - Collection caching for performance
    - Automatic collection creation
    """

    def __init__(self, storage_path: str = "./data/chromadb"):
        """
        Initialize ChromaDB persistent client.

        Args:
            storage_path: Path to ChromaDB storage directory
        """
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
