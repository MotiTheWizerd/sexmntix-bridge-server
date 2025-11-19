"""
Text builder utility for vector storage operations.
"""
from typing import Dict, Any


class TextBuilder:
    """
    Utility for building embedding text from memory units.
    """
    def build_embedding_text_from_memory_unit(self, memory_unit: Dict[str, Any]) -> str:
        """
        Build natural language embedding text from Gemini memory unit.

        Combines: topic + summary + key_points + tags + related_topics + reflection
        into a single semantic paragraph for clean embedding.

        Args:
            memory_unit: Gemini-enriched memory object

        Returns:
            Natural language text ready for embedding
        """
        parts = []

        # Topic (title/subject)
        if topic := memory_unit.get("topic"):
            parts.append(topic + ".")

        # Summary (main content)
        if summary := memory_unit.get("summary"):
            parts.append(summary)

        # Key points (as natural list)
        if key_points := memory_unit.get("key_points"):
            if isinstance(key_points, list):
                parts.append(" ".join(key_points))

        # Tags (semantic labels)
        if tags := memory_unit.get("tags"):
            if isinstance(tags, list):
                parts.append(f"Tags: {', '.join(tags)}.")

        # Related topics (connections)
        if related_topics := memory_unit.get("related_topics"):
            if isinstance(related_topics, list):
                parts.append(f"Related topics: {', '.join(related_topics)}.")

        # Reflection (meta-cognitive insight)
        if reflection := memory_unit.get("reflection"):
            parts.append(f"Reflection: {reflection}")

        # Join into natural paragraph with spaces
        return " ".join(parts)