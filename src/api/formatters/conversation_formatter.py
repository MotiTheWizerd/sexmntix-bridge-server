"""
Conversation formatter for presentation logic.

Handles transformation of raw data to API response formats.
Extracted from conversations.py routes following formatter pattern.
"""

from typing import List, Dict, Any
from src.api.schemas.conversation import ConversationSearchResult


class ConversationFormatter:
    """
    Formatter for conversation presentation logic.

    Provides static methods to transform raw conversation data
    into API response formats.
    """

    @staticmethod
    def format_search_results(results: List[Dict[str, Any]]) -> List[ConversationSearchResult]:
        """
        Format raw vector search results to ConversationSearchResult schema.

        Transforms ChromaDB search results into structured Pydantic models
        for API response.

        Args:
            results: List of raw search result dicts with id, document, metadata, distance, similarity

        Returns:
            List of ConversationSearchResult Pydantic models
        """
        search_results = []
        for result in results:
            # Extract conversation_id from metadata
            conversation_id = result.get("metadata", {}).get("conversation_id")

            search_results.append(
                ConversationSearchResult(
                    id=result["id"],
                    conversation_id=conversation_id,
                    document=result["document"],
                    metadata=result["metadata"],
                    distance=result["distance"],
                    similarity=result["similarity"]
                )
            )

        return search_results

    @staticmethod
    def format_memory_response(synthesized_memory: str) -> Dict[str, str]:
        """
        Format synthesized memory string as JSON response.

        Args:
            synthesized_memory: Natural language memory from LLM synthesis

        Returns:
            Dictionary with 'synthesized_memory' key
        """
        return {"synthesized_memory": synthesized_memory}
