"""
Collection Management

Handles ChromaDB collection operations: create, retrieve, list, and delete.
Includes collection caching for performance.
"""

from typing import Optional
import chromadb
from chromadb import Collection
from src.modules.core.telemetry.logger import get_logger
from .naming_strategy import create_collection_name
from .config import ChromaDBConfig, DEFAULT_CONFIG

logger = get_logger(__name__)


class CollectionManager:
    """
    Manages ChromaDB collections with caching and isolation support.

    Features:
    - Get or create collections with user/project isolation
    - Collection caching for performance
    - List all collections with version compatibility
    - Delete collections with cache invalidation
    - Metadata storage for isolation tracking
    """

    def __init__(
        self,
        chromadb_client: chromadb.PersistentClient,
        config: ChromaDBConfig = DEFAULT_CONFIG
    ):
        """
        Initialize collection manager.

        Args:
            chromadb_client: ChromaDB PersistentClient instance
            config: ChromaDB configuration (default: DEFAULT_CONFIG)
        """
        self.client = chromadb_client
        self.config = config
        self.logger = logger

        # Collection cache for performance
        self._collections: dict[str, Collection] = {}

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
        if collection_prefix is None:
            collection_prefix = self.config.default_collection_prefix

        # Create collection name using hash
        collection_name = create_collection_name(
            user_id,
            project_id,
            collection_prefix,
            self.config
        )

        self.logger.info(
            f"[COLLECTION_MANAGER] Getting collection: {collection_name} for user_id={user_id}, project_id={project_id}"
        )

        # Return cached collection if available
        if collection_name in self._collections:
            self.logger.debug(
                f"[COLLECTION_MANAGER] Returning cached collection: {collection_name}"
            )
            return self._collections[collection_name]

        # Create or get collection
        collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"user_id": user_id, "project_id": project_id}
        )

        # Cache for future use
        self._collections[collection_name] = collection

        self.logger.info(
            f"[COLLECTION_MANAGER] Collection created/retrieved: {collection_name}, item count: {collection.count()}"
        )

        return collection

    def list_collections(self) -> list[str]:
        """
        List all collection names in the database.

        Returns:
            List of collection names

        Note:
            Handles version compatibility for ChromaDB.
            v0.6.0+ returns collection names (strings) directly.
            Earlier versions return collection objects with .name attribute.
        """
        collections = self.client.list_collections()

        # Handle empty collections list
        if not collections:
            return []

        # ChromaDB v0.6.0+ returns collection names (strings) directly
        # Earlier versions returned collection objects with .name attribute
        if isinstance(collections[0], str):
            return collections
        else:
            # Fallback for older versions
            return [col.name for col in collections]

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
        if collection_prefix is None:
            collection_prefix = self.config.default_collection_prefix

        # Create collection name using hash
        collection_name = create_collection_name(
            user_id,
            project_id,
            collection_prefix,
            self.config
        )

        self.logger.info(
            f"[COLLECTION_MANAGER] Deleting collection: {collection_name}"
        )

        # Remove from cache
        if collection_name in self._collections:
            del self._collections[collection_name]

        # Delete from ChromaDB
        self.client.delete_collection(collection_name)

        self.logger.info(f"[COLLECTION_MANAGER] Collection deleted: {collection_name}")

    def clear_cache(self) -> None:
        """Clear all cached collections."""
        self.logger.debug("[COLLECTION_MANAGER] Clearing collection cache")
        self._collections.clear()
