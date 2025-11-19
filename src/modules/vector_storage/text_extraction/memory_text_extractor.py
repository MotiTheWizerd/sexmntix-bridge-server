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
        - code_context: Key patterns, API surface, dependencies
        - semantic_context: Domain concepts, technical patterns, integration points
        - future_planning: Next logical steps
        - outcomes: Performance impact, test coverage, technical debt
        - complexity: Technical, business, coordination complexity

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

        if "component" in memory_data:
            parts.append(memory_data["component"])

        # Solution details
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

        # Root cause
        if "root_cause" in memory_data:
            parts.append(memory_data["root_cause"])

        # Complexity metrics
        if "complexity" in memory_data and isinstance(memory_data["complexity"], dict):
            complexity = memory_data["complexity"]
            if "technical" in complexity:
                parts.append(complexity["technical"])
            if "business" in complexity:
                parts.append(complexity["business"])
            if "coordination" in complexity:
                parts.append(complexity["coordination"])

        # Outcomes
        if "outcomes" in memory_data and isinstance(memory_data["outcomes"], dict):
            outcomes = memory_data["outcomes"]
            if "performance_impact" in outcomes:
                parts.append(outcomes["performance_impact"])
            if "test_coverage_delta" in outcomes:
                parts.append(outcomes["test_coverage_delta"])
            if "technical_debt_reduced" in outcomes:
                parts.append(outcomes["technical_debt_reduced"])

        # Code context
        if "code_context" in memory_data and isinstance(memory_data["code_context"], dict):
            code_context = memory_data["code_context"]
            if "key_patterns" in code_context and isinstance(code_context["key_patterns"], list):
                parts.extend(code_context["key_patterns"][:10])  # Limit to first 10
            if "api_surface" in code_context and isinstance(code_context["api_surface"], list):
                parts.extend(code_context["api_surface"][:10])  # Limit to first 10
            if "dependencies_added" in code_context and isinstance(code_context["dependencies_added"], list):
                parts.extend(code_context["dependencies_added"])
            if "breaking_changes" in code_context and isinstance(code_context["breaking_changes"], list):
                parts.extend(code_context["breaking_changes"])

        # Semantic context
        if "semantic_context" in memory_data and isinstance(memory_data["semantic_context"], dict):
            semantic_context = memory_data["semantic_context"]
            if "domain_concepts" in semantic_context and isinstance(semantic_context["domain_concepts"], list):
                parts.extend(semantic_context["domain_concepts"])
            if "technical_patterns" in semantic_context and isinstance(semantic_context["technical_patterns"], list):
                parts.extend(semantic_context["technical_patterns"])
            if "integration_points" in semantic_context and isinstance(semantic_context["integration_points"], list):
                parts.extend(semantic_context["integration_points"])

        # Future planning
        if "future_planning" in memory_data and isinstance(memory_data["future_planning"], dict):
            future_planning = memory_data["future_planning"]
            if "next_logical_steps" in future_planning and isinstance(future_planning["next_logical_steps"], list):
                parts.extend(future_planning["next_logical_steps"][:5])  # Limit to first 5
            if "architecture_decisions" in future_planning and isinstance(future_planning["architecture_decisions"], dict):
                # Add decision names and rationales
                for decision, rationale in future_planning["architecture_decisions"].items():
                    parts.append(f"{decision}: {rationale}")
            if "extension_points" in future_planning and isinstance(future_planning["extension_points"], list):
                parts.extend(future_planning["extension_points"][:5])  # Limit to first 5

        # Tags
        if "tags" in memory_data and isinstance(memory_data["tags"], list):
            parts.append(" ".join(memory_data["tags"]))

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

        # Validation
        if "validation" in memory_data:
            parts.append(memory_data["validation"])

        # Files touched (for context)
        if "files_touched" in memory_data and isinstance(memory_data["files_touched"], list):
            # Add file paths as context
            parts.extend(memory_data["files_touched"][:10])  # Limit to first 10

        # Related tasks
        if "related_tasks" in memory_data and isinstance(memory_data["related_tasks"], list):
            parts.extend(memory_data["related_tasks"])

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
