"""
Default prompt for basic semantic grouping (legacy support).
"""


def build_default_prompt(message: str) -> str:
    """
    Build a default prompt for semantic grouping.
    Legacy support for basic semantic grouping functionality.
    Args:
        message: The message to process
    Returns:
        Simple prompt for grouping related content
    """
    return f"""Analyze the following message and group related content together semantically:
{message}
Please identify and group related topics, concepts, or discussion points."""
