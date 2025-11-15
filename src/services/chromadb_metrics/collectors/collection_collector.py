"""
Collection metrics collector

Gathers metrics about ChromaDB collections, vector counts, and metadata.
"""

from typing import Dict, Any, List
from src.modules.core import Logger
from src.infrastructure.chromadb.client import ChromaDBClient


class CollectionMetricsCollector:
    """Collects metrics about ChromaDB collections"""

    def __init__(self, chromadb_client: ChromaDBClient, logger: Logger):
        """Initialize collection metrics collector

        Args:
            chromadb_client: ChromaDB client instance
            logger: Logger instance
        """
        self.chromadb_client = chromadb_client
        self.logger = logger

    async def get_collection_metrics(self) -> Dict[str, Any]:
        """Get metrics about ChromaDB collections

        Returns:
            Dictionary with collection counts, vector counts, and details
        """
        try:
            collections = self.chromadb_client.list_collections()

            collection_details = []
            total_vectors = 0

            for col_name in collections:
                try:
                    # Get collection to access count and metadata
                    collection = self.chromadb_client.client.get_collection(col_name)
                    vector_count = collection.count()
                    total_vectors += vector_count

                    collection_details.append({
                        "collection_name": col_name,
                        "vector_count": vector_count,
                        "metadata": collection.metadata,
                        "user_id": collection.metadata.get("user_id", "unknown"),
                        "project_id": collection.metadata.get("project_id", "unknown"),
                    })
                except Exception as e:
                    self.logger.warning(f"Error getting collection {col_name}: {e}")

            # Sort by vector count (largest first)
            collection_details.sort(key=lambda x: x["vector_count"], reverse=True)

            return {
                "total_collections": len(collections),
                "total_vectors": total_vectors,
                "collections": collection_details,
                "largest_collection": collection_details[0] if collection_details else None,
                "smallest_collection": collection_details[-1] if collection_details else None,
                "avg_vectors_per_collection": total_vectors / len(collections) if collections else 0,
            }
        except Exception as e:
            self.logger.error(f"Error getting collection metrics: {e}")
            return {
                "total_collections": 0,
                "total_vectors": 0,
                "collections": [],
                "error": str(e),
            }
