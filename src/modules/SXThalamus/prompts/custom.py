"""
Custom template-based prompt builder.
"""

from typing import Any


def build_custom_prompt(template: str, **kwargs: Any) -> str:
    """
    Build a custom prompt from a template string.

    Args:
        template: Template string with {variable} placeholders
        **kwargs: Keyword arguments to substitute into the template

    Returns:
        Formatted prompt with variables substituted

    Example:
        >>> template = "Analyze this {content_type}: {content}"
        >>> build_custom_prompt(template, content_type="code", content="def hello(): pass")
        "Analyze this code: def hello(): pass"
    """
    return template.format(**kwargs)
