"""Prompt templates and builders for BasicAgent"""

from typing import Dict, Any


class PromptBuilder:
    """
    Builds prompts for Gemini API requests.

    Centralizes all prompt templates and formatting logic.
    """

    @staticmethod
    def build_semantic_chunking_prompt(conversation_text: str) -> str:
        """
        Build a prompt for semantic chunking of conversation text.

        This prompt instructs Gemini to split a conversation into minimal
        semantic units, where each chunk expresses exactly one idea.

        Args:
            conversation_text: The conversation to analyze and chunk

        Returns:
            Formatted prompt for semantic chunking
        """
        return f"""Analyze this conversation and split it into minimal semantic units.

Each chunk should express exactly one complete idea or topic. Return the result as a JSON array where each element is an object with:
- "chunk_id": sequential number
- "topic": brief topic description
- "content": the actual text chunk
- "summary": one-sentence summary

Conversation:
{conversation_text}

Return ONLY the JSON array, no additional text."""

    @staticmethod
    def build_custom_prompt(template: str, **kwargs: Any) -> str:
        """
        Build a custom prompt from a template with variable substitution.

        Args:
            template: Prompt template with {variable} placeholders
            **kwargs: Variables to substitute in the template

        Returns:
            Formatted prompt with variables substituted

        Example:
            >>> builder = PromptBuilder()
            >>> template = "Analyze this: {text}"
            >>> prompt = builder.build_custom_prompt(template, text="Hello")
        """
        return template.format(**kwargs)

    @staticmethod
    def build_summarization_prompt(text: str, max_words: int = 100) -> str:
        """
        Build a prompt for text summarization.

        Args:
            text: The text to summarize
            max_words: Maximum words in summary (default: 200)

        Returns:
            Formatted prompt for summarization
        """
        return f"""Summarize the following text in {max_words} words or less.
Be concise and capture the main points.

Text:
{text}"""

    @staticmethod
    def build_extraction_prompt(text: str, fields: Dict[str, str]) -> str:
        """
        Build a prompt for structured data extraction.

        Args:
            text: The text to extract data from
            fields: Dict of field names and descriptions to extract

        Returns:
            Formatted prompt for data extraction

        Example:
           {
                    "memory_id": "uuid",
                    "group_id": 3,
                    "topic": "Detailed Log Analysis and System Architecture",

                    "summary": "Assistant provides deep architectural interpretation of the system logs: DB persistence, vectorization pipeline, event flow, and background LLM processing.",

                    "key_points": [
                        "PostgreSQL write completed instantly",
                        "Async vectorization scheduled",
                        "Event bus firing SXThalamus",
                        "Gemini processing in ~30ms",
                        "Architecture validated end-to-end",
                        "Close to first SYNÆON memory loop"
                    ],

                    "importance": "high",
                    "worldview_relevance": 0.95,

                    "chunk": {
                        "start_marker": "assistant: Everything looks **exactly right** in that log.",
                        "end_marker": "Keep going.",
                        "content_preview": "Everything looks exactly right in that log...",
                        "raw_text": null
                    },

                    "metadata": {
                        "timestamp": "2025-11-16T16:30:40Z",
                        "source": "conversation",
                        "user_id": 1,
                        "session_id": 101,
                        "message_index_start": 12,
                        "message_index_end": 15
                    },

                    "vector": null
                    }
        """
        fields_description = "\n".join([
            f'- "{field}": {description}'
            for field, description in fields.items()
        ])

        return f"""Extract the following fields from the text and return as JSON:

{fields_description}

Text:
{text}

Return ONLY the JSON object, no additional text."""
