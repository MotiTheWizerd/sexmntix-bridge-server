"""
Memory log response formatters.

Provides presentation layer formatting for memory log search results:
- JSON format for WebUI/API consumers
- Plain text format for terminal/CLI usage
"""
from typing import List, Dict, Any
from fastapi.responses import PlainTextResponse
from src.api.schemas.memory_log import MemoryLogSearchResult


class MemoryLogFormatter:
    """Formats memory log search results for different output formats."""

    @staticmethod
    def format_search_results_json(results: List[Dict[str, Any]]) -> List[MemoryLogSearchResult]:
        """
        Format search results as JSON (for WebUI/API).

        Args:
            results: Raw search results from vector service

        Returns:
            List of MemoryLogSearchResult schemas
        """
        search_results = []
        for result in results:
            # Extract memory_log_id from the memory_id format: memory_{id}_{user}_{project}
            # Handle both integer IDs and UUID strings
            memory_id_parts = result["id"].split("_")
            if len(memory_id_parts) > 1:
                try:
                    memory_log_id = int(memory_id_parts[1])
                except ValueError:
                    # If not an integer, keep as string (UUID from MCP tools)
                    memory_log_id = memory_id_parts[1]
            else:
                memory_log_id = None

            search_results.append(
                MemoryLogSearchResult(
                    id=result["id"],
                    memory_log_id=memory_log_id,
                    document=result["document"],
                    metadata=result["metadata"],
                    distance=result["distance"],
                    similarity=result["similarity"]
                )
            )
        return search_results

    @staticmethod
    def format_search_results_text(
        results: List[MemoryLogSearchResult],
        query: str
    ) -> PlainTextResponse:
        """
        Format search results as plain text (for terminal/CLI).

        Args:
            results: List of search results
            query: Original search query

        Returns:
            PlainTextResponse with formatted text
        """
        lines = [
            "=" * 80,
            f"SEARCH RESULTS - {len(results)} items",
            f'Query: "{query}"',
            "=" * 80,
            ""
        ]

        for idx, result in enumerate(results, 1):
            doc = result.document
            task = doc.get("task", "untitled-memory")

            lines.append(f"[{idx}/{len(results)}] {task}")
            lines.append("-" * 80)
            lines.append(f"Similarity: {result.similarity * 100:.1f}%")

            if doc.get("component"):
                lines.append(f"Component: {doc['component']}")

            if doc.get("date"):
                date_str = str(doc['date']).split("T")[0]
                lines.append(f"Date: {date_str}")

            if doc.get("tags"):
                tag_str = ", ".join(doc['tags'][:5])
                lines.append(f"Tags: {tag_str}")

            lines.append("")
            if doc.get("summary"):
                summary = doc['summary']
                if len(summary) > 200:
                    summary = summary[:197] + "..."
                lines.append(summary)

            lines.append("")

        lines.append("=" * 80)
        lines.append("End of Results")
        lines.append("=" * 80)

        formatted_text = "\n".join(lines)
        return PlainTextResponse(content=formatted_text)

    @staticmethod
    def format_date_search_text(
        results: List[MemoryLogSearchResult],
        query: str,
        time_period_str: str
    ) -> PlainTextResponse:
        """
        Format date-filtered search results as plain text.

        Args:
            results: List of search results
            query: Original search query
            time_period_str: Human-readable time period description

        Returns:
            PlainTextResponse with formatted text
        """
        lines = [
            "=" * 80,
            f"DATE-FILTERED SEARCH RESULTS - {len(results)} items",
            f'Query: "{query}"',
            f'Time Period: {time_period_str}',
            "=" * 80,
            ""
        ]

        for idx, result in enumerate(results, 1):
            doc = result.document
            task = doc.get("task", "untitled-memory")

            lines.append(f"[{idx}/{len(results)}] {task}")
            lines.append("-" * 80)
            lines.append(f"Similarity: {result.similarity * 100:.1f}%")

            if doc.get("component"):
                lines.append(f"Component: {doc['component']}")

            if doc.get("date"):
                date_str = str(doc['date']).split("T")[0]
                lines.append(f"Date: {date_str}")

            if doc.get("tags"):
                tag_str = ", ".join(doc['tags'][:5])
                lines.append(f"Tags: {tag_str}")

            lines.append("")
            if doc.get("summary"):
                summary = doc['summary']
                if len(summary) > 200:
                    summary = summary[:197] + "..."
                lines.append(summary)

            lines.append("")

        lines.append("=" * 80)
        lines.append("End of Results")
        lines.append("=" * 80)

        formatted_text = "\n".join(lines)
        return PlainTextResponse(content=formatted_text)

    @staticmethod
    def format_mcp_search_results_text(
        query: str,
        results: List[Dict[str, Any]],
        filters_applied: Dict[str, Any]
    ) -> str:
        """
        Format search results as plain text for MCP tools (returns string, not PlainTextResponse).

        Args:
            query: The search query
            results: List of search result dicts from vector service
            filters_applied: Filter parameters used (min_similarity, limit, etc.)

        Returns:
            Formatted text string for terminal display
        """
        total = len(results)

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
        if filters_applied.get("limit"):
            filter_parts.append(f"limit={filters_applied['limit']}")

        if filter_parts:
            lines.append(f"Filters: {', '.join(filter_parts)}")

        lines.append("=" * 80)
        lines.append("")

        # Results
        for idx, result in enumerate(results, 1):
            doc = result.get("document", {})
            metadata = result.get("metadata", {})

            # Task name (from document or metadata)
            task = doc.get("task") or metadata.get("task", "untitled-memory")

            # Result header
            lines.append(f"[{idx}/{total}] {task}")
            lines.append("-" * 80)

            # Similarity score
            similarity = result.get("similarity", 0.0)
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
