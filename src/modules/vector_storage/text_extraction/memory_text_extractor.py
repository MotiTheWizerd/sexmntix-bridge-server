"""
Memory Text Extractor

Produces a curated, JSON-serialized payload that will be embedded for memory
logs. Only semantic, high-signal fields are included to keep embeddings clean.
"""

from typing import Dict, Any
from src.modules.core import Logger
from .text_cleaner import TextCleaner
from .embedding_payload import EmbeddingPayloadBuilder


class MemoryTextExtractor:
    """
    Extracts searchable text from memory log data using the curated payload
    format:
    - summary
    - root_cause
    - lesson
    - gotchas (issue/solution pairs)
    - solution (approach + key_changes)
    - tags
    - component
    - semantic_context (domain/technical patterns)
    - code_context (api_surface/key_patterns)
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
        Build the curated payload and serialize it for embedding.

        Args:
            memory_data: Memory log data dictionary

        Returns:
            Curated payload serialized as compact JSON (max 60K chars)
        """
        payload = EmbeddingPayloadBuilder.build(memory_data)
        if not payload:
            return ""

        serialized = EmbeddingPayloadBuilder.serialize(payload)

        truncated = TextCleaner.smart_truncate(
            serialized,
            max_chars=TextCleaner.MAX_EMBEDDING_CHARS,
            preserve_sentences=False
        )

        return truncated.strip()

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
                f"No curated embedding payload for memory_log_id: {memory_log_id}"
            )
            fallback_text = memory_data.get("task", "untitled")
            searchable_text = TextCleaner.smart_truncate(
                str(fallback_text),
                max_chars=TextCleaner.MAX_EMBEDDING_CHARS,
                preserve_sentences=False
            ).strip()

        return searchable_text
