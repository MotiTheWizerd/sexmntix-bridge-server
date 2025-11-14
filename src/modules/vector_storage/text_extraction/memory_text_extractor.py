"""
Memory Text Extractor

Single Responsibility: Extract searchable text from memory log data structures.

This component knows how to navigate memory log data and combine relevant fields
into a single searchable text string for embedding generation.
"""

from typing import Dict, Any
from src.modules.core import Logger


class MemoryTextExtractor:
    """
    Extracts searchable text from memory log data.

    Combines multiple fields for rich semantic context:
    - task: Main task description
    - summary: High-level summary
    - solution: Implementation details
    - tags: Keywords
    - component: Component name
    - root_cause: Root cause description
    - gotchas: Issue/solution pairs (up to 5)
    - lesson: Key lesson learned
    """

    def __init__(self, logger: Logger):
        """
        Initialize the text extractor.

        Args:
            logger: Logger instance
        """
        self.logger = logger

    def extract_searchable_text(self, memory_data: Dict[str, Any]) -> str:
        """
        Extract searchable text from memory log data.

        Combines multiple fields for rich semantic context:
        - task: Main task description
        - summary: High-level summary
        - solution: Implementation details (approach + key_changes)
        - tags: Keywords
        - component: Component name
        - root_cause: Root cause description
        - gotchas: Issue/solution pairs for important edge cases
        - lesson: Key lesson learned

        Args:
            memory_data: Memory log data dictionary

        Returns:
            Combined searchable text string
        """
        parts = []

        # Core fields
        if "task" in memory_data:
            parts.append(memory_data["task"])

        if "summary" in memory_data:
            parts.append(memory_data["summary"])

        if "solution" in memory_data:
            solution = memory_data["solution"]
            if isinstance(solution, dict):
                # Handle nested solution object
                if "approach" in solution:
                    parts.append(solution["approach"])
                if "key_changes" in solution and isinstance(solution["key_changes"], list):
                    parts.extend(solution["key_changes"][:5])  # Limit to first 5
            elif isinstance(solution, str):
                parts.append(solution)

        # Tags
        if "tags" in memory_data and isinstance(memory_data["tags"], list):
            parts.append(" ".join(memory_data["tags"]))

        # Component
        if "component" in memory_data:
            parts.append(memory_data["component"])

        # Root cause
        if "root_cause" in memory_data:
            parts.append(memory_data["root_cause"])

        # Gotchas - important for finding memories by edge cases and issues
        if "gotchas" in memory_data and isinstance(memory_data["gotchas"], list):
            for gotcha in memory_data["gotchas"][:5]:  # Limit to first 5 gotchas
                if isinstance(gotcha, dict):
                    # Include both issue and solution for full context
                    if "issue" in gotcha:
                        parts.append(gotcha["issue"])
                    if "solution" in gotcha:
                        parts.append(gotcha["solution"])

        # Lesson - key takeaway that summarizes learning
        if "lesson" in memory_data:
            parts.append(memory_data["lesson"])

        # Combine with spaces
        searchable_text = " ".join(parts)

        return searchable_text.strip()

    def extract_with_fallback(
        self,
        memory_data: Dict[str, Any],
        memory_log_id: int
    ) -> str:
        """
        Extract searchable text with fallback to task or default.

        If extraction produces empty text, falls back to:
        1. memory_data["task"] if available
        2. "untitled" as last resort

        Args:
            memory_data: Memory log data dictionary
            memory_log_id: ID for logging purposes

        Returns:
            Non-empty searchable text string
        """
        searchable_text = self.extract_searchable_text(memory_data)

        if not searchable_text:
            self.logger.warning(
                f"No searchable text for memory_log_id: {memory_log_id}"
            )
            searchable_text = memory_data.get("task", "untitled")

        return searchable_text
