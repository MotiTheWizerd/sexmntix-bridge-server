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
    def format_as_terminal_text(
        query: str,
        formatted_results: List[Dict[str, Any]],
        filters_applied: Dict[str, Any]
    ) -> str:
        """Format search results as clean terminal text output

        Args:
            query: The search query
            formatted_results: List of formatted result dicts
            filters_applied: Filter parameters used

        Returns:
            Formatted text string for terminal display
        """
        total = len(formatted_results)

        # Header
        lines = [
            "=" * 80,
            f"SEARCH RESULTS - {total} items",
            f'Query: "{query}"'
        ]

        # Add filters if present
        filter_parts = []
        if filters_applied.get("min_similarity", 0) > 0:
            filter_parts.append(f"min_similarity={filters_applied['min_similarity']}")
        if "time_period" in filters_applied:
            filter_parts.append(f"time_period={filters_applied['time_period']}")

        if filter_parts:
            lines.append(f"Filters: {', '.join(filter_parts)}")

        lines.append("=" * 80)
        lines.append("")

        # Results
        for idx, result in enumerate(formatted_results, 1):
            doc = result.get("document", {})
            metadata = result.get("metadata", {})

            # Task name (from document or metadata)
            task = doc.get("task") or metadata.get("task", "untitled-memory")

            # Result header
            lines.append(f"[{idx}/{total}] {task}")
            lines.append("-" * 80)

            # Similarity score
            similarity = result.get("similarity_score", 0.0)
            similarity_pct = similarity * 100
            lines.append(f"Similarity: {similarity_pct:.1f}%")

            # Component
            component = doc.get("component") or metadata.get("component")
            if component:
                lines.append(f"Component: {component}")

            # Date
            date = doc.get("date")
            if date:
                # Extract just the date part if it's an ISO string
                date_str = str(date).split("T")[0] if "T" in str(date) else str(date)
                lines.append(f"Date: {date_str}")

            # Task (if different from title)
            if doc.get("task") and doc.get("task") != task:
                lines.append(f"Task: {doc.get('task')}")

            # Tags
            tags = doc.get("tags", [])
            if tags:
                tag_str = ", ".join(tags[:5])  # Max 5 tags
                lines.append(f"Tags: {tag_str}")

            # Summary/content
            lines.append("")
            summary = doc.get("summary", "")
            if summary:
                # Truncate to reasonable length
                if len(summary) > 200:
                    summary = summary[:197] + "..."
                lines.append(summary)

            lines.append("")

        # Footer
        lines.append("=" * 80)
        lines.append("End of Results")
        lines.append("=" * 80)

        return "\n".join(lines)

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
