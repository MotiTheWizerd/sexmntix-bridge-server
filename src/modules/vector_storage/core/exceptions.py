"""
Custom exceptions for vector storage operations.
"""


class VectorStorageError(Exception):
    """Base exception for vector storage operations."""
    pass


class InvalidTextError(VectorStorageError):
    """Raised when searchable text is empty or invalid."""
    pass


class ProviderError(VectorStorageError):
    """Raised when embedding provider operations fail."""
    pass


class MemoryNotFoundError(VectorStorageError):
    """Raised when a requested memory is not found."""
    pass


class ConversationNotFoundError(VectorStorageError):
    """Raised when a requested conversation is not found."""
    pass


class NoteNotFoundError(VectorStorageError):
    """Raised when a requested note is not found."""
    pass