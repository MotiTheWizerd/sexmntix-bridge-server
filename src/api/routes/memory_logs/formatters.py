"""
Memory log formatters - Transform search results into different output formats.
"""
from typing import List, Dict, Any
from src.api.schemas.memory_log import MemoryLogSearchResult


class MemoryLogFormatter:
    """Formatter for memory log search results."""

    @staticmethod
    def format_json(results: List[Dict[str, Any]]) -> List[MemoryLogSearchResult]:
        """
        Format search results as full JSON objects.

        Returns all fields including nested objects like complexity, code_context,
        future_planning, etc. Best for programmatic access or detailed analysis.

        Args:
            results: Raw search results from service

        Returns:
            List of full MemoryLogSearchResult objects
        """
        return [
            MemoryLogSearchResult(
                id=result.get("id", ""),
                memory_log_id=result.get("memory_log_id"),
                document=result.get("document", {}),
                metadata=result.get("metadata", {}),
                distance=result.get("distance", 0.0),
                similarity=result.get("similarity", 0.0)
            )
            for result in results
        ]

    @staticmethod
    def format_text(results: List[Dict[str, Any]], query: str) -> str:
        """
        Format search results as beautiful terminal text output.

        Creates formatted text with headers, separators, and structured display
        of each result. Perfect for terminal/CLI usage.

        Args:
            results: Raw search results from service
            query: Original search query

        Returns:
            Formatted text string
        """
        lines = []

        # Header
        lines.append("=" * 80)
        lines.append(f"SEARCH RESULTS - {len(results)} items")
        lines.append("=" * 80)
        lines.append("")

        # Each result
        for i, result in enumerate(results, 1):
            document = result.get("document", {})
            metadata = result.get("metadata", {})
            similarity = result.get("similarity", 0.0)

            # Extract fields
            task = metadata.get("task") or document.get("task") or "untitled"
            component = document.get("component", "")
            tags = document.get("tags") or metadata.get("tags") or []
            summary = document.get("summary") or document.get("lesson") or document.get("content", "")
            created_at = metadata.get("created_at", "")

            # Format date
            date_str = created_at.split("T")[0] if created_at else ""

            # Result header
            lines.append(f"[{i}/{len(results)}] {task}")
            lines.append("-" * 80)
            lines.append(f"Similarity: {similarity * 100:.1f}%")
            if component:
                lines.append(f"Component: {component}")
            if date_str:
                lines.append(f"Date: {date_str}")
            if task and task != "untitled":
                lines.append(f"Task: {task}")
            if tags:
                tags_str = ", ".join(tags) if isinstance(tags, list) else tags
                lines.append(f"Tags: {tags_str}")
            lines.append("")

            # Summary
            if summary:
                lines.append(summary)

            lines.append("")

        # Footer
        lines.append("=" * 80)
        lines.append("End of Results")
        lines.append("=" * 80)

        return "\n".join(lines)
