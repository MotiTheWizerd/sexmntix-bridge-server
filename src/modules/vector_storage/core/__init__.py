"""
Core types and exceptions for vector storage operations.
"""

from src.modules.vector_storage.core.types import (
    MemorySearchRequest,
    MemorySearchResult,
    VectorStorageComponent,
)
from src.modules.vector_storage.core.exceptions import (
    VectorStorageError,
    InvalidTextError,
    ProviderError,
    MemoryNotFoundError,
    ConversationNotFoundError,
    NoteNotFoundError,
)

__all__ = [
    # Types
    "MemorySearchRequest",
    "MemorySearchResult",
    "VectorStorageComponent",
    # Exceptions
    "VectorStorageError",
    "InvalidTextError",
    "ProviderError",
    "MemoryNotFoundError",
    "ConversationNotFoundError",
    "NoteNotFoundError",
]