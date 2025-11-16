"""Prompt templates for SXThalamus semantic chunking"""

from typing import Dict, Any


class SXThalamusPromptBuilder:
    """
    Builds prompts for semantic conversation grouping and chunking.

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
        return f"""Analyze this AI conversation and semantically group the content for intelligent chunking.

Your task:
1. Identify distinct topics and themes in the conversation
2. Group related content together based on semantic meaning
3. Suggest chunk boundaries that preserve context
4. Provide metadata for each semantic group

Return your response as a JSON array where each element represents a semantic group with:
- "group_id": sequential number
- "topic": brief topic/theme description
- "summary": one-sentence summary of the group
- "key_points": array of main points discussed
- "chunk_boundaries": array of objects with:
  - "start_marker": indicator of where chunk starts
  - "end_marker": indicator of where chunk ends
  - "content_preview": first 100 characters
  - "importance": "high", "medium", or "low"

Conversation to analyze:
{conversation_text}

Return ONLY the JSON array, no additional text or explanation."""

    @staticmethod
    def build_default_prompt(message: str) -> str:
        """
        Build the default prompt for semantic grouping (legacy support).

        Args:
            message: The message to process

        Returns:
            Formatted prompt for Gemini
        """
        return f"""Analyze and semantically group the following AI message to prepare it for better chunking. Identify logical sections and group related content:

{message}"""

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
        return template.format(**kwargs)
