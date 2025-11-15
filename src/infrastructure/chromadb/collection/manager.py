"""
Collection Manager

Facade that coordinates collection cache and operations.
Provides the main public API for collection management.
"""

from typing import Optional
import chromadb
from chromadb import Collection
from src.modules.core.telemetry.logger import get_logger
from ..core.config import ChromaDBConfig, DEFAULT_CONFIG
from ..core.naming_strategy import create_collection_name
from .cache import CollectionCache
from .operations import CollectionOperations

logger = get_logger(__name__)


class CollectionManager:
    """
    Manages ChromaDB collections with caching and isolation support.

    This is a facade that coordinates:
    - CollectionCache: In-memory caching for performance
    - CollectionOperations: CRUD operations on ChromaDB
    - Naming strategy: User/project isolation via hashed names

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

        # Initialize cache and operations components
        self._cache = CollectionCache()
        self._operations = CollectionOperations(chromadb_client, config)

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

        # Check cache first
        cached_collection = self._cache.get(collection_name)
        if cached_collection:
            self.logger.debug(
                f"[COLLECTION_MANAGER] Returning cached collection: {collection_name}"
            )
            return cached_collection

        # Get or create collection from ChromaDB
        collection = self._operations.get_or_create(
            collection_name,
            metadata={"user_id": user_id, "project_id": project_id}
        )

        # Cache for future use
        self._cache.set(collection_name, collection)

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
        return self._operations.list()

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

        # Remove from cache first
        self._cache.delete(collection_name)

        # Delete from ChromaDB
        self._operations.delete(collection_name)

        self.logger.info(f"[COLLECTION_MANAGER] Collection deleted: {collection_name}")

    def clear_cache(self) -> None:
        """Clear all cached collections."""
        self.logger.debug("[COLLECTION_MANAGER] Clearing collection cache")
        self._cache.clear()
