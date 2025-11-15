"""
Collection Operations

Handles core CRUD operations for ChromaDB collections.
Encapsulates direct ChromaDB client interactions.
"""

from typing import Optional
import chromadb
from chromadb import Collection
from src.modules.core.telemetry.logger import get_logger
from ..core.config import ChromaDBConfig, DEFAULT_CONFIG

logger = get_logger(__name__)


class CollectionOperations:
    """
    Handles ChromaDB collection CRUD operations.

    Features:
    - Get or create collections
    - List all collections with version compatibility
    - Delete collections
    - Direct ChromaDB client interaction
    """

    def __init__(
        self,
        chromadb_client: chromadb.PersistentClient,
        config: ChromaDBConfig = DEFAULT_CONFIG
    ):
        """
        Initialize collection operations.

        Args:
            chromadb_client: ChromaDB PersistentClient instance
            config: ChromaDB configuration (default: DEFAULT_CONFIG)
        """
        self.client = chromadb_client
        self.config = config
        self.logger = logger

    def get_or_create(
        self,
        collection_name: str,
        metadata: Optional[dict] = None
    ) -> Collection:
        """
        Get an existing collection or create a new one.

        Args:
            collection_name: Name of the collection
            metadata: Optional metadata to store with the collection

        Returns:
            ChromaDB Collection instance
        """
        self.logger.info(
            f"[COLLECTION_OPERATIONS] Getting or creating collection: {collection_name}"
        )

        collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata=metadata or {}
        )

        self.logger.info(
            f"[COLLECTION_OPERATIONS] Collection ready: {collection_name}, count: {collection.count()}"
        )

        return collection

    def list(self) -> list[str]:
        """
        List all collection names in the database.

        Returns:
            List of collection names

        Note:
            Handles version compatibility for ChromaDB.
            v0.6.0+ returns collection names (strings) directly.
            Earlier versions return collection objects with .name attribute.
        """
        self.logger.debug("[COLLECTION_OPERATIONS] Listing all collections")

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

    def delete(self, collection_name: str) -> None:
        """
        Delete a collection from ChromaDB.

        Args:
            collection_name: Name of the collection to delete
        """
        self.logger.info(
            f"[COLLECTION_OPERATIONS] Deleting collection: {collection_name}"
        )

        self.client.delete_collection(collection_name)

        self.logger.info(
            f"[COLLECTION_OPERATIONS] Collection deleted: {collection_name}"
        )
