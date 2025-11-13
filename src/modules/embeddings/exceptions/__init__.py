"""
Custom exceptions for the embeddings module.
"""

from .exceptions import (
    EmbeddingError,
    ProviderError,
    APIRateLimitError,
    InvalidTextError,
    ProviderConnectionError,
    ProviderTimeoutError,
)

__all__ = [
    "EmbeddingError",
    "ProviderError",
    "APIRateLimitError",
    "InvalidTextError",
    "ProviderConnectionError",
    "ProviderTimeoutError",
]
