"""File Storage Infrastructure

Handles custom file-based storage for conversations and other data.
"""

from .conversation_storage import ConversationFileStorage

__all__ = [
    "ConversationFileStorage",
]
