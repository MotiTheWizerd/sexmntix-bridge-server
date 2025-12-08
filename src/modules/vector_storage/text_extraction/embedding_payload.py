"""
Embedding payload builder.

Creates the minimal, high-signal payload that will be serialized and
embedded for memory logs. Keeps semantic content only and drops noisy
metadata so embeddings stay focused on reasoning and fixes.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional


class EmbeddingPayloadBuilder:
    """Builds curated payloads for memory log embeddings."""

    MAX_GOTCHAS = 5
    MAX_KEY_CHANGES = 5
    MAX_TAGS = 10
    MAX_LIST_ITEMS = 10

    @classmethod
    def build(cls, memory_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a curated payload containing only semantic fields.

        Args:
            memory_data: Raw memory log dictionary.

        Returns:
            Dict containing only the fields we want to embed.
        """
        payload: Dict[str, Any] = {}

        cls._assign_string(payload, "lesson", memory_data.get("lesson"))
        cls._assign_string(payload, "summary", memory_data.get("summary"))
        cls._assign_string(payload, "root_cause", memory_data.get("root_cause"))
        cls._assign_string(payload, "component", memory_data.get("component"))

        gotchas = cls._extract_gotchas(memory_data.get("gotchas"))
        if gotchas:
            payload["gotchas"] = gotchas

        solution = cls._extract_solution(memory_data.get("solution"))
        if solution:
            payload["solution"] = solution

        tags = cls._extract_string_list(memory_data.get("tags"), limit=cls.MAX_TAGS)
        if tags:
            payload["tags"] = tags

        semantic_context = cls._extract_semantic_context(memory_data.get("semantic_context"))
        if semantic_context:
            payload["semantic_context"] = semantic_context

        code_context = cls._extract_code_context(memory_data.get("code_context"))
        if code_context:
            payload["code_context"] = code_context

        return payload

    @staticmethod
    def serialize(payload: Dict[str, Any]) -> str:
        """
        Serialize payload deterministically for embedding.

        Args:
            payload: Curated payload dictionary.

        Returns:
            Compact JSON string with sorted keys.
        """
        return json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True)

    # ---- helpers -----------------------------------------------------------------

    @staticmethod
    def _assign_string(target: Dict[str, Any], field: str, value: Any):
        """Assign a trimmed string into target if present."""
        text = EmbeddingPayloadBuilder._coerce_string(value)
        if text:
            target[field] = text

    @staticmethod
    def _coerce_string(value: Any) -> Optional[str]:
        """Convert value to trimmed string if possible."""
        if value is None:
            return None
        if isinstance(value, str):
            text = value.strip()
            return text or None
        return str(value).strip() or None

    @classmethod
    def _extract_string_list(cls, value: Any, limit: int) -> List[str]:
        """Extract list of trimmed strings with length limit."""
        if not isinstance(value, list):
            return []
        items: List[str] = []
        for raw in value:
            if len(items) >= limit:
                break
            text = cls._coerce_string(raw)
            if text:
                items.append(text)
        return items

    @classmethod
    def _extract_gotchas(cls, gotchas_value: Any) -> List[Dict[str, str]]:
        """Extract structured gotcha entries."""
        if not isinstance(gotchas_value, list):
            return []

        extracted: List[Dict[str, str]] = []
        for gotcha in gotchas_value:
            if len(extracted) >= cls.MAX_GOTCHAS:
                break
            if not isinstance(gotcha, dict):
                continue

            issue = cls._coerce_string(gotcha.get("issue"))
            solution = cls._coerce_string(gotcha.get("solution"))

            if not issue and not solution:
                continue

            entry: Dict[str, str] = {}
            if issue:
                entry["issue"] = issue
            if solution:
                entry["solution"] = solution

            # Preserve optional metadata when meaningful
            category = cls._coerce_string(gotcha.get("category"))
            severity = cls._coerce_string(gotcha.get("severity"))
            if category:
                entry["category"] = category
            if severity:
                entry["severity"] = severity

            extracted.append(entry)

        return extracted

    @classmethod
    def _extract_solution(cls, solution_value: Any) -> Dict[str, Any]:
        """Extract approach and key changes."""
        if not solution_value:
            return {}

        solution: Dict[str, Any] = {}

        if isinstance(solution_value, str):
            text = cls._coerce_string(solution_value)
            if text:
                solution["approach"] = text
            return solution

        if isinstance(solution_value, dict):
            cls._assign_string(solution, "approach", solution_value.get("approach"))

            key_changes = cls._extract_string_list(
                solution_value.get("key_changes"),
                limit=cls.MAX_KEY_CHANGES
            )
            if key_changes:
                solution["key_changes"] = key_changes

        return solution

    @classmethod
    def _extract_semantic_context(cls, semantic_value: Any) -> Dict[str, Any]:
        """Extract domain/technical context fields."""
        if not isinstance(semantic_value, dict):
            return {}

        context: Dict[str, Any] = {}
        domain = cls._extract_string_list(
            semantic_value.get("domain_concepts"),
            limit=cls.MAX_LIST_ITEMS
        )
        if domain:
            context["domain_concepts"] = domain

        technical = cls._extract_string_list(
            semantic_value.get("technical_patterns"),
            limit=cls.MAX_LIST_ITEMS
        )
        if technical:
            context["technical_patterns"] = technical

        return context

    @classmethod
    def _extract_code_context(cls, code_value: Any) -> Dict[str, Any]:
        """Extract API surface and key patterns."""
        if not isinstance(code_value, dict):
            return {}

        context: Dict[str, Any] = {}
        api_surface = cls._extract_string_list(
            code_value.get("api_surface"),
            limit=cls.MAX_LIST_ITEMS
        )
        if api_surface:
            context["api_surface"] = api_surface

        key_patterns = cls._extract_string_list(
            code_value.get("key_patterns"),
            limit=cls.MAX_LIST_ITEMS
        )
        if key_patterns:
            context["key_patterns"] = key_patterns

        return context
