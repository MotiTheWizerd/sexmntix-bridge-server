"""
Result formatting utilities for embedding tool

Provides functions to format and structure embedding results for client consumption.
"""

from typing import Dict, Any, List


class EmbeddingResultFormatter:
    """Formats embedding generation results for optimal readability and structure"""

    # Constants
    EMBEDDING_SAMPLE_SIZE = 5

    @classmethod
    def format_embedding_result(
        cls,
        text: str,
        embedding_result: Any,
        return_full_vector: bool
    ) -> Dict[str, Any]:
        """Format embedding generation result

        Args:
            text: Original input text
            embedding_result: Result from embedding service
            return_full_vector: Whether to include full vector in response

        Returns:
            Formatted result dictionary with embedding data and metadata
        """
        response_data = {
            "text": text,
            "model": embedding_result.model,
            "provider": embedding_result.provider,
            "dimensions": embedding_result.dimensions,
            "cached": embedding_result.cached,
            "metadata": cls._build_metadata(text, embedding_result)
        }

        # Include full vector or sample based on flag
        if return_full_vector:
            response_data["embedding"] = embedding_result.embedding
            response_data["message"] = "Embedding vector generated successfully"
        else:
            response_data["embedding_sample"] = cls._create_embedding_sample(
                embedding_result.embedding
            )
            response_data["message"] = (
                "Embedding generated successfully. Use 'return_full_vector: true' "
                "to get the complete vector."
            )

        return response_data

    @staticmethod
    def _build_metadata(text: str, embedding_result: Any) -> Dict[str, Any]:
        """Build metadata for embedding result

        Args:
            text: Original input text
            embedding_result: Result from embedding service

        Returns:
            Metadata dictionary with text length and generation time
        """
        return {
            "text_length": len(text),
            "generation_time": embedding_result.metadata.get("generation_time_ms", 0)
        }

    @classmethod
    def _create_embedding_sample(cls, embedding: List[float]) -> List[float]:
        """Create a sample of the embedding vector for preview

        Args:
            embedding: Full embedding vector

        Returns:
            First N values of the embedding vector
        """
        if not embedding:
            return []
        return embedding[:cls.EMBEDDING_SAMPLE_SIZE]

    @staticmethod
    def create_response_metadata(user_id: str, project_id: str) -> Dict[str, Any]:
        """Create response metadata

        Args:
            user_id: User ID for the request
            project_id: Project ID for the request

        Returns:
            Metadata dictionary
        """
        return {
            "user_id": user_id,
            "project_id": project_id
        }
