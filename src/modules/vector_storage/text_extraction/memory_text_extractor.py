"""
Memory Text Extractor

Single Responsibility: Extract searchable text from memory log data structures.

This component knows how to navigate memory log data and combine relevant fields
into a single searchable text string for embedding generation.

Uses structured field formatting with proper cleaning, deduplication, and truncation.
"""

from typing import Dict, Any, List, Tuple
from src.modules.core import Logger
from .text_cleaner import TextCleaner


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
        Extract searchable text from memory log data with structured formatting.

        Uses field-preserving format: "Field Name: value. Another Field: value."
        Implements the target embedding strategy:
        - Selective embedding of semantic fields only
        - Structured text with field labels
        - Gotcha formatting: "Gotcha: Issue: X. Solution: Y."
        - Smart truncation at 60K characters
        - Deduplication and cleaning

        Embedded fields (semantic content):
        - summary: High-level summary
        - root_cause: Why the problem occurred
        - lesson: What was learned
        - gotchas: Issue/solution pairs
        - domain_concepts: Semantic context
        - technical_patterns: Architectural patterns

        Args:
            memory_data: Memory log data dictionary

        Returns:
            Combined searchable text string (max 60K chars)
        """
        # Use structured fields with labels for better semantic understanding
        fields = self._extract_structured_fields(memory_data)

        # Smart truncate with field preservation
        searchable_text = TextCleaner.smart_truncate_with_fields(
            fields,
            max_chars=TextCleaner.MAX_EMBEDDING_CHARS
        )

        return searchable_text.strip()

    def _extract_structured_fields(self, memory_data: Dict[str, Any]) -> List[Tuple[str, str]]:
        """
        Extract fields in structured format with labels.

        Returns list of (field_name, field_value) tuples in priority order.
        Higher priority fields appear first to ensure inclusion if truncation needed.

        Args:
            memory_data: Memory log data dictionary

        Returns:
            List of (field_name, field_value) tuples
        """
        fields = []

        # PRIORITY 1: Core semantic fields (always include)
        if "summary" in memory_data and memory_data["summary"]:
            fields.append(("Summary", str(memory_data["summary"])))

        if "root_cause" in memory_data and memory_data["root_cause"]:
            fields.append(("Root Cause", str(memory_data["root_cause"])))

        if "lesson" in memory_data and memory_data["lesson"]:
            fields.append(("Lesson", str(memory_data["lesson"])))

        # PRIORITY 2: Gotchas with structured formatting
        gotchas_text = self._format_gotchas(memory_data.get("gotchas", []))
        if gotchas_text:
            fields.append(("Gotchas", gotchas_text))

        # PRIORITY 3: Semantic context
        if "semantic_context" in memory_data and isinstance(memory_data["semantic_context"], dict):
            semantic_context = memory_data["semantic_context"]

            if "domain_concepts" in semantic_context and isinstance(semantic_context["domain_concepts"], list):
                concepts = ", ".join(semantic_context["domain_concepts"])
                if concepts:
                    fields.append(("Domain Concepts", concepts))

            if "technical_patterns" in semantic_context and isinstance(semantic_context["technical_patterns"], list):
                patterns = ", ".join(semantic_context["technical_patterns"])
                if patterns:
                    fields.append(("Technical Patterns", patterns))

            if "integration_points" in semantic_context and isinstance(semantic_context["integration_points"], list):
                integration = ", ".join(semantic_context["integration_points"])
                if integration:
                    fields.append(("Integration Points", integration))

        # PRIORITY 4: Task and component context
        if "task" in memory_data and memory_data["task"]:
            fields.append(("Task", str(memory_data["task"])))

        if "component" in memory_data and memory_data["component"]:
            fields.append(("Component", str(memory_data["component"])))

        # PRIORITY 5: Solution details
        solution_text = self._format_solution(memory_data.get("solution"))
        if solution_text:
            fields.append(("Solution", solution_text))

        # PRIORITY 6: Code context
        if "code_context" in memory_data and isinstance(memory_data["code_context"], dict):
            code_context = memory_data["code_context"]

            if "key_patterns" in code_context and isinstance(code_context["key_patterns"], list):
                patterns = ", ".join(code_context["key_patterns"][:10])
                if patterns:
                    fields.append(("Key Patterns", patterns))

            if "api_surface" in code_context and isinstance(code_context["api_surface"], list):
                apis = ", ".join(code_context["api_surface"][:10])
                if apis:
                    fields.append(("API Surface", apis))

        # PRIORITY 7: Outcomes
        if "outcomes" in memory_data and isinstance(memory_data["outcomes"], dict):
            outcomes = memory_data["outcomes"]
            outcomes_parts = []

            if "performance_impact" in outcomes and outcomes["performance_impact"]:
                outcomes_parts.append(f"Performance: {outcomes['performance_impact']}")
            if "test_coverage_delta" in outcomes and outcomes["test_coverage_delta"]:
                outcomes_parts.append(f"Test Coverage: {outcomes['test_coverage_delta']}")
            if "technical_debt_reduced" in outcomes and outcomes["technical_debt_reduced"]:
                outcomes_parts.append(f"Technical Debt: {outcomes['technical_debt_reduced']}")

            if outcomes_parts:
                fields.append(("Outcomes", ". ".join(outcomes_parts)))

        # PRIORITY 8: Future planning
        if "future_planning" in memory_data and isinstance(memory_data["future_planning"], dict):
            future_planning = memory_data["future_planning"]

            if "next_logical_steps" in future_planning and isinstance(future_planning["next_logical_steps"], list):
                steps = ", ".join(future_planning["next_logical_steps"][:5])
                if steps:
                    fields.append(("Next Steps", steps))

            if "extension_points" in future_planning and isinstance(future_planning["extension_points"], list):
                extensions = ", ".join(future_planning["extension_points"][:5])
                if extensions:
                    fields.append(("Extension Points", extensions))

        # PRIORITY 9: Validation
        if "validation" in memory_data and memory_data["validation"]:
            fields.append(("Validation", str(memory_data["validation"])))

        # PRIORITY 10: Tags
        if "tags" in memory_data and isinstance(memory_data["tags"], list):
            tags = ", ".join(memory_data["tags"])
            if tags:
                fields.append(("Tags", tags))

        return fields

    def _format_gotchas(self, gotchas: list) -> str:
        """
        Format gotchas with structured "Issue: X. Solution: Y." format.

        Args:
            gotchas: List of gotcha dictionaries

        Returns:
            Formatted gotchas string
        """
        if not gotchas or not isinstance(gotchas, list):
            return ""

        formatted_gotchas = []

        for gotcha in gotchas[:5]:  # Limit to first 5
            if not isinstance(gotcha, dict):
                continue

            parts = []

            # Include category and severity if available
            category = gotcha.get("category", "")
            severity = gotcha.get("severity", "")

            if category or severity:
                label = f"[{category}]" if category else ""
                if severity:
                    label += f" [{severity}]" if label else f"[{severity}]"
                if label:
                    parts.append(label.strip())

            # Format issue and solution
            issue = gotcha.get("issue", "").strip()
            solution = gotcha.get("solution", "").strip()

            if issue:
                parts.append(f"Issue: {issue}")
            if solution:
                parts.append(f"Solution: {solution}")

            if parts:
                formatted_gotchas.append(" - ".join(parts))

        return " | ".join(formatted_gotchas)

    def _format_solution(self, solution) -> str:
        """
        Format solution field into readable text.

        Args:
            solution: Solution data (dict or string)

        Returns:
            Formatted solution string
        """
        if not solution:
            return ""

        if isinstance(solution, str):
            return solution

        if isinstance(solution, dict):
            parts = []

            if "approach" in solution and solution["approach"]:
                parts.append(f"Approach: {solution['approach']}")

            if "key_changes" in solution and isinstance(solution["key_changes"], list):
                changes = ", ".join(solution["key_changes"][:5])
                if changes:
                    parts.append(f"Key Changes: {changes}")

            return ". ".join(parts)

        return ""

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
