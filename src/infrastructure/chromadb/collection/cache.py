"""
Collection Cache

Provides in-memory caching for ChromaDB collections to improve performance.
"""

from typing import Optional
from chromadb import Collection
from src.modules.core.telemetry.logger import get_logger

logger = get_logger(__name__)


class CollectionCache:
    """
    In-memory cache for ChromaDB collections.

    Features:
    - Fast retrieval of previously accessed collections
    - Cache invalidation support
    - Memory-efficient storage with dict
    """

    def __init__(self):
        """Initialize empty collection cache."""
        self._collections: dict[str, Collection] = {}

    def get(self, collection_name: str) -> Optional[Collection]:
        """
        Retrieve a collection from cache.

        Args:
            collection_name: Name of the collection

        Returns:
            Collection if cached, None otherwise
        """
        collection = self._collections.get(collection_name)
        if collection:
            logger.debug(f"[COLLECTION_CACHE] Cache hit: {collection_name}")
        return collection

    def set(self, collection_name: str, collection: Collection) -> None:
        """
        Store a collection in cache.

        Args:
            collection_name: Name of the collection
            collection: Collection instance to cache
        """
        self._collections[collection_name] = collection
        logger.debug(f"[COLLECTION_CACHE] Cached: {collection_name}")

    def delete(self, collection_name: str) -> None:
        """
        Remove a collection from cache.

        Args:
            collection_name: Name of the collection to remove
        """
        if collection_name in self._collections:
            del self._collections[collection_name]
            logger.debug(f"[COLLECTION_CACHE] Removed from cache: {collection_name}")

    def clear(self) -> None:
        """Clear all cached collections."""
        logger.debug("[COLLECTION_CACHE] Clearing all cached collections")
        self._collections.clear()

    def contains(self, collection_name: str) -> bool:
        """
        Check if a collection is cached.

        Args:
            collection_name: Name of the collection

        Returns:
            True if cached, False otherwise
        """
        return collection_name in self._collections
