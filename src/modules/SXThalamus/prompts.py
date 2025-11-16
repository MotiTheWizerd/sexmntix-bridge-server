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



## Instructions ##
Memory Unit Instructions (Real-Time Vectorization)
Assign a unique memory_id for each unit.
Set group_id based on semantic grouping of messages.
Fill topic, summary, and key_points with short, factual descriptions of what the chunk represents.
Set importance to low, medium, or high based on how essential the information is.
Set worldview_relevance to a numeric score (0–1) that reflects long-term value.
Create embedding_text by concatenating the raw conversation lines covered by the chunk (exact text between start and end markers).
Set vector to null.
Background workers will embed and update this field.
Fill chunk_boundaries with:
start_marker
end_marker
content_preview
importance (local importance for the chunk)
Add metadata with:
timestamp
source (e.g., "conversation")
session_id
Return the final object exactly in this format for each chunk.

## Example ##
  {{
    "group_id": 1,
    "topic": "Initial Greetings and System Logging",
    "summary": "The conversation starts with a greeting, followed by system logs indicating conversation storage and processing.",
     "reflection": "User is preparing to create parallel conversations, indicating upcoming multi-threaded workflow or testing phase."
     "key_points": [
      "Initial greeting exchange.",
      "System logs confirm conversation storage and Gemini processing.",
      "Indicates the system is running smoothly."
    ],
    "chunk_boundaries": [
      {{
        "start_marker": "user: hi",
        "end_marker": "INFO:     127.0.0.1:62566 - \"POST /conversations HTTP/1.1\" 201 Created",
        "content_preview": "hi",
        "importance": "medium"
      }}
    ]
  }},
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

{message} """

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
