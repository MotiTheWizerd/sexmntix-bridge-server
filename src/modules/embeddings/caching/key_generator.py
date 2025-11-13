"""
Cache key generation utilities.
"""

import hashlib


def generate_cache_key(text: str, model: str) -> str:
    """
    Generate cache key from text and model.

    Args:
        text: Input text
        model: Model name

    Returns:
        Cache key as hex string
    """
    content = f"{model}:{text}"
    return hashlib.sha256(content.encode()).hexdigest()
