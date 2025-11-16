"""Message processing utilities for SXThalamus"""

from typing import List, Dict, Any


def combine_conversation_messages(messages: List[Dict[str, Any]]) -> str:
    """
    Combine conversation messages into a single text string.

    Args:
        messages: List of message dicts with 'role' and 'text' fields

    Returns:
        Combined text with role prefixes

    Example:
        >>> messages = [
        ...     {"role": "user", "text": "Hello"},
        ...     {"role": "assistant", "text": "Hi there!"}
        ... ]
        >>> combine_conversation_messages(messages)
        'user: Hello\\n\\nassistant: Hi there!'
    """
    combined = []
    for msg in messages:
        role = msg.get("role", "unknown")
        text = msg.get("text", "")
        combined.append(f"{role}: {text}")

    return "\n\n".join(combined)
