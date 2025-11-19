"""
SXThalamus prompt functions and orchestrator.

This module contains all prompt building functions used by the SXThalamus service,
plus the SXThalamusPromptBuilder orchestrator class.
"""

from typing import Any

from .semantic_grouping import build_semantic_grouping_prompt
from .default import build_default_prompt
from .custom import build_custom_prompt


class SXThalamusPromptBuilder:
    """
    Orchestrator for building prompts for semantic conversation grouping and chunking.

    This class acts as a loader/orchestrator that delegates to individual prompt
    builder functions. All prompt implementations are located in this prompts/ folder.

    Specialized prompts for analyzing AI conversations and splitting them
    into semantically meaningful chunks for better storage and retrieval.
    """

    @staticmethod
    def build_semantic_grouping_prompt(conversation_text: str) -> str:
        """
        Build a prompt for semantic grouping of conversation text.

        This prompt instructs the LLM to analyze a conversation and group
        content into semantic units for intelligent chunking and storage.

        Args:
            conversation_text: The conversation to analyze and group

        Returns:
            Formatted prompt for semantic grouping
        """
        return build_semantic_grouping_prompt(conversation_text)

    @staticmethod
    def build_default_prompt(message: str) -> str:
        """
        Build the default prompt for semantic grouping (legacy support).

        Args:
            message: The message to process

        Returns:
            Formatted prompt for Gemini
        """
        return build_default_prompt(message)

    @staticmethod
    def build_custom_prompt(template: str, **kwargs: Any) -> str:
        """
        Build a custom prompt from a template with variable substitution.

        Args:
            template: Prompt template with {variable} placeholders
            **kwargs: Variables to substitute in the template

        Returns:
            Formatted prompt with variables substituted
        """
        return build_custom_prompt(template, **kwargs)


__all__ = [
    "build_semantic_grouping_prompt",
    "build_default_prompt",
    "build_custom_prompt",
    "SXThalamusPromptBuilder",
]
