"""
Mental note formatters - Transform search results into different output formats.
"""
from typing import List, Dict, Any
from src.api.schemas.mental_note import MentalNoteSearchResult


class MentalNoteFormatter:
    """Formatter for mental note search results."""

    @staticmethod
    def format_json(results: List[Dict[str, Any]]) -> List[MentalNoteSearchResult]:
        """
        Format search results as full JSON objects.

        Returns all fields including document (content, note_type, session_id)
        and metadata. Best for programmatic access or detailed analysis.

        Args:
            results: Raw search results from service

        Returns:
            List of full MentalNoteSearchResult objects
        """
        return [
            MentalNoteSearchResult(
                id=result.get("id", ""),
                mental_note_id=result.get("mental_note_id"),
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
        lines.append(f"MENTAL NOTES SEARCH RESULTS - {len(results)} items")
        lines.append("=" * 80)
        lines.append("")

        # Each result
        for i, result in enumerate(results, 1):
            document = result.get("document", {})
            metadata = result.get("metadata", {})
            similarity = result.get("similarity", 0.0)

            # Extract fields
            content = document.get("content", "")
            note_type = document.get("note_type", "note")
            session_id = document.get("session_id", "")
            created_at = document.get("created_at", "")

            # Format date
            date_str = created_at.split("T")[0] if created_at else ""

            # Result header
            lines.append(f"[{i}/{len(results)}] {note_type.upper()}")
            lines.append("-" * 80)
            lines.append(f"Similarity: {similarity * 100:.1f}%")
            if session_id:
                lines.append(f"Session: {session_id}")
            if date_str:
                lines.append(f"Date: {date_str}")
            lines.append("")

            # Content
            if content:
                lines.append(content)

            lines.append("")

        # Footer
        lines.append("=" * 80)
        lines.append("End of Results")
        lines.append("=" * 80)

        return "\n".join(lines)
