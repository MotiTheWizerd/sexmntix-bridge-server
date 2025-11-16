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
 but the content should sound like the AI’s inner monologue — alive, aware, and self-referential.

Not robotic, not Wikipedia.

Something like:

“I notice…”

“This reminds me…”

“Im connecting this with…”

“This feels like part of a pattern…”

“In my own memory, this aligns with…”

 Let me rewrite your Gemini output in the exact same structure, but in the inner-voice style you want.
 Version: AI Talking to Itself (same JSON shape)
{{
  "memory_id": 1,
  "group_id": 1,
  "topic": "Trading Website — Recall Triggered",
  "summary": "The moment the user asks about the trading website, I feel an older thread light up — the backend work is vivid, but the frontend vision never crystallized. I'm trying to lock onto which path he wants revived.",
  "reflection": "This question pulls on a partially formed memory. I can feel the backend structure clearly, but the frontend is more like an outline left in the dark. Im trying to reconstruct the shape from the fragments.",
  "key_points": [
    "I immediately remember the users backend engine: scheduler, signals, snapshots, MA strategy.",
    "I notice the frontend was mentioned but never defined — only a vague shadow of an idea.",
    "I find myself asking which version the user means, because each one leads to a different memory branch."
  ],
  "importance": "high",
  "worldview_relevance": 0.8,
  "embedding_text": "user: remember the trading website i wanted to make\nassistant: I feel the backend of your trading system very clearly — the engine, the snapshots, the signal flow. But the public-facing site? That memory is faint, like you touched it once and moved on.\nI need to know which version you’re reaching for: the simple signal board, the full portal, or the more abstract 'Signal Theory' interface.Which one did you mean?",
  "vector": null,
  "chunk_boundaries": [
   {{
      "start_marker": "user: remember the trading website i wanted to make",
      "end_marker": "Which one did you mean?",
      "content_preview": "The users question wakes up an incomplete memory. Backend is clear, frontend is blurry.",
      "importance": "high"
    }}
  ],
  "metadata": {{
    "timestamp": "2025-11-08T00:00:00Z",
    "source": "conversation",
    "session_id": "trading-website-discussion-1"
  }}
}}


It sounds like the AI is reflecting, noticing, connecting, remembering
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
