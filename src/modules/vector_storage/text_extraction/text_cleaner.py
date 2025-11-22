"""
Text Cleaning Utilities

Provides utilities for cleaning, normalizing, and preparing text for embedding.
Includes deduplication, whitespace normalization, and smart truncation.
"""

import re
from typing import List, Optional


class TextCleaner:
    """
    Utilities for cleaning and normalizing text before embedding.

    Features:
    - Deduplication of repeated content
    - Whitespace normalization
    - Smart truncation with field preservation
    """

    MAX_EMBEDDING_CHARS = 60_000  # Google API limit

    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """
        Normalize whitespace in text.

        - Replace multiple spaces with single space
        - Replace tabs with spaces
        - Replace multiple newlines with single newline
        - Strip leading/trailing whitespace

        Args:
            text: Input text

        Returns:
            Normalized text
        """
        if not text:
            return ""

        # Replace tabs with spaces
        text = text.replace('\t', ' ')

        # Replace multiple spaces with single space
        text = re.sub(r' +', ' ', text)

        # Replace multiple newlines with single newline
        text = re.sub(r'\n+', '\n', text)

        # Strip leading/trailing whitespace
        text = text.strip()

        return text

    @staticmethod
    def deduplicate_content(parts: List[str]) -> List[str]:
        """
        Remove duplicate strings from list while preserving order.

        Uses case-insensitive comparison to catch duplicates.

        Args:
            parts: List of text parts

        Returns:
            Deduplicated list
        """
        if not parts:
            return []

        seen = set()
        unique_parts = []

        for part in parts:
            # Normalize for comparison
            normalized = part.lower().strip()

            if normalized and normalized not in seen:
                seen.add(normalized)
                unique_parts.append(part)

        return unique_parts

    @staticmethod
    def smart_truncate(
        text: str,
        max_chars: int = MAX_EMBEDDING_CHARS,
        preserve_sentences: bool = True
    ) -> str:
        """
        Intelligently truncate text to maximum character limit.

        Attempts to preserve complete sentences if possible.

        Args:
            text: Input text
            max_chars: Maximum character limit (default: 60,000)
            preserve_sentences: Whether to try preserving complete sentences

        Returns:
            Truncated text
        """
        if not text or len(text) <= max_chars:
            return text

        if not preserve_sentences:
            # Simple truncation
            return text[:max_chars].rstrip()

        # Try to find last sentence boundary before limit
        truncated = text[:max_chars]

        # Look for sentence endings (. ! ? followed by space or newline)
        sentence_endings = [
            truncated.rfind('. '),
            truncated.rfind('.\n'),
            truncated.rfind('! '),
            truncated.rfind('!\n'),
            truncated.rfind('? '),
            truncated.rfind('?\n')
        ]

        # Find the rightmost sentence ending
        last_sentence_end = max(sentence_endings)

        if last_sentence_end > max_chars * 0.8:  # Only use if we keep at least 80%
            return truncated[:last_sentence_end + 1].rstrip()

        # Fallback to simple truncation
        return truncated.rstrip()

    @staticmethod
    def smart_truncate_with_fields(
        fields: List[tuple[str, str]],
        max_chars: int = MAX_EMBEDDING_CHARS
    ) -> str:
        """
        Truncate structured fields while preserving complete fields.

        Adds fields one by one until character limit is reached.
        Ensures at least the first field is always included (truncated if needed).

        Args:
            fields: List of (field_name, field_value) tuples
            max_chars: Maximum character limit

        Returns:
            Combined text with complete fields
        """
        if not fields:
            return ""

        result_parts = []
        current_length = 0

        for i, (field_name, field_value) in enumerate(fields):
            # Format field
            formatted = f"{field_name}: {field_value}"
            field_length = len(formatted)

            # First field always included (truncated if too long)
            if i == 0:
                if field_length > max_chars:
                    # Truncate first field to fit
                    available = max_chars - len(f"{field_name}: ")
                    truncated_value = field_value[:available].rstrip()
                    result_parts.append(f"{field_name}: {truncated_value}")
                    break
                else:
                    result_parts.append(formatted)
                    current_length = field_length
                    continue

            # Check if adding this field would exceed limit
            # Add 2 for ". " separator
            separator_length = 2 if result_parts else 0
            total_length = current_length + separator_length + field_length

            if total_length > max_chars:
                # Can't fit this field, stop here
                break

            result_parts.append(formatted)
            current_length = total_length

        return ". ".join(result_parts)

    @staticmethod
    def clean_and_join(parts: List[str], separator: str = " ") -> str:
        """
        Clean, deduplicate, and join text parts.

        Args:
            parts: List of text parts
            separator: String to join parts with

        Returns:
            Cleaned and joined text
        """
        # Filter empty strings
        parts = [p for p in parts if p and p.strip()]

        # Normalize whitespace in each part
        parts = [TextCleaner.normalize_whitespace(p) for p in parts]

        # Deduplicate
        parts = TextCleaner.deduplicate_content(parts)

        # Join
        return separator.join(parts)
