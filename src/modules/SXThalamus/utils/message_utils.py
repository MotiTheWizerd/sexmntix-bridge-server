"""Message processing utilities for SXThalamus"""

from typing import List, Dict, Any, Optional


def combine_conversation_messages(
    messages: List[Dict[str, Any]],
    role_filter: Optional[str] = None
) -> str:
    """
    Combine conversation messages into a single text string.

    Args:
        messages: List of message dicts with 'role' and 'text' fields
        role_filter: Optional role to filter by (e.g., "assistant", "user")
                     If provided, only messages with matching role are included

    Returns:
        Combined text with role prefixes

    Example:
        >>> messages = [
        ...     {"role": "user", "text": "Hello"},
        ...     {"role": "assistant", "text": "Hi there!"}
        ... ]
        >>> combine_conversation_messages(messages)
        'user: Hello\\n\\nassistant: Hi there!'
        >>> combine_conversation_messages(messages, role_filter="assistant")
        'assistant: Hi there!'
    """
    combined = []
    for msg in messages:
        role = msg.get("role", "unknown")
        text = msg.get("text", "")

        # Filter by role if specified
        if role_filter and role != role_filter:
            continue

        combined.append(f"{role}: {text}")

    return "\n\n".join(combined)
