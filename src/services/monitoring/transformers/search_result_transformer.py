"""
Search Result Transformer

Handles transformation of ChromaDB search results to API response format.
Eliminates code duplication across search endpoints.
"""

from typing import List, Dict, Any, Optional
from src.api.schemas.chromadb_viewer import DocumentResponse


class SearchResultTransformer:
    """Transforms ChromaDB search results to DocumentResponse objects"""

    @staticmethod
    def transform_results(
        ids: List[str],
        documents: List[Any],
        metadatas: List[Dict[str, Any]],
        distances: List[float],
        embeddings: Optional[List[List[float]]] = None,
        min_similarity: float = 0.0,
    ) -> List[DocumentResponse]:
        """
        Transform ChromaDB search results into DocumentResponse objects.

        Args:
            ids: List of document IDs
            documents: List of document content
            metadatas: List of document metadata
            distances: List of distance scores
            embeddings: Optional list of embedding vectors
            min_similarity: Minimum similarity threshold (0.0-1.0)

        Returns:
            List of DocumentResponse objects filtered by min_similarity
        """
        results = []
        embeddings = embeddings or []

        for i, doc_id in enumerate(ids):
            distance = distances[i] if i < len(distances) else 0.0
            similarity = SearchResultTransformer.distance_to_similarity(distance)

            # Apply similarity filter
            if similarity < min_similarity:
                continue

            doc_response = DocumentResponse(
                id=doc_id,
                document=documents[i] if i < len(documents) else {},
                metadata=metadatas[i] if i < len(metadatas) else {},
                embedding=embeddings[i] if i < len(embeddings) else None,
                distance=distance,
                similarity=similarity
            )
            results.append(doc_response)

        return results

    @staticmethod
    def distance_to_similarity(distance: float) -> float:
        """
        Convert ChromaDB distance score to similarity score.

        ChromaDB returns distances where 0 = perfect match.
        We convert to similarity where 1.0 = perfect match.

        Args:
            distance: Distance score from ChromaDB (0 = perfect match)

        Returns:
            Similarity score (1.0 = perfect match)
        """
        return 1.0 - distance
