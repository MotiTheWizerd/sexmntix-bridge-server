"""
Result formatting utilities for semantic search tool

Provides functions to format and structure search results for client consumption.
"""

from typing import List, Dict, Any


class SearchResultFormatter:
    """Formats semantic search results for optimal readability and structure"""

    @staticmethod
    def format_search_result(result: Dict[str, Any]) -> Dict[str, Any]:
        """Format a single search result

        Args:
            result: Raw search result from vector storage

        Returns:
            Formatted result dictionary with standardized structure
        """
        document = result.get("document", {})

        return {
            "memory_id": result.get("id"),
            "content": document.get("content", ""),
            "similarity_score": round(result.get("distance", 0.0), 4),
            "metadata": result.get("metadata", {}),
            "document": document,  # Include full document for reference
            "created_at": result.get("metadata", {}).get("created_at")
        }

    @classmethod
    def format_search_results(cls, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format multiple search results

        Args:
            results: List of raw search results from vector storage

        Returns:
            List of formatted result dictionaries
        """
        return [cls.format_search_result(result) for result in results]

    @staticmethod
    def create_response_data(
        query: str,
        formatted_results: List[Dict[str, Any]],
        min_similarity: float,
        limit: int,
        user_id: str,
        project_id: str
    ) -> Dict[str, Any]:
        """Create the complete response data structure

        Args:
            query: The original search query
            formatted_results: List of formatted search results
            min_similarity: Minimum similarity threshold used
            limit: Maximum number of results requested
            user_id: User ID for the search
            project_id: Project ID for the search

        Returns:
            Complete response data dictionary with results and metadata
        """
        return {
            "data": {
                "query": query,
                "result_count": len(formatted_results),
                "results": formatted_results,
                "filters_applied": {
                    "min_similarity": min_similarity,
                    "limit": limit
                }
            },
            "metadata": {
                "user_id": user_id,
                "project_id": project_id
            }
        }
