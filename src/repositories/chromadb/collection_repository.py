"""
ChromaDB Collection Repository

Abstracts direct ChromaDB collection access.
Provides a clean interface for collection operations.
"""

from typing import Any

from src.infrastructure.chromadb.client import ChromaDBClient


class CollectionRepository:
    """Repository for ChromaDB collection operations"""

    def __init__(self, chromadb_client: ChromaDBClient):
        self.chromadb_client = chromadb_client

    def get_collection(self, collection_name: str) -> Any:
        """
        Get a ChromaDB collection by name.

        Args:
            collection_name: Name of the collection

        Returns:
            ChromaDB collection object

        Raises:
            Exception: If collection does not exist
        """
        return self.chromadb_client.client.get_collection(collection_name)
