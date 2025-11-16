"""
Internal event handlers for memory log, mental note, and conversation storage.

Refactored into modular components for better maintainability,
testability, and adherence to Single Responsibility Principle.

Architecture:
- config.py: Configuration and constants
- validators.py: Event data validation
- formatters.py: Logging message formatters
- orchestrators.py: Vector storage orchestration
- utils/db_updater.py: PostgreSQL embedding updates
- handlers/: Handler implementations
  - base_handler.py: Base class with template method pattern
  - memory_log_handler.py: Memory log specific handler
  - mental_note_handler.py: Mental note specific handler
  - conversation_handler.py: Conversation specific handler
"""

from .handlers.memory_log_handler import MemoryLogStorageHandler
from .handlers.mental_note_handler import MentalNoteStorageHandler
from .handlers.conversation_handler import ConversationStorageHandler

# Backward compatibility aliases for existing code
# This allows gradual migration from old class names to new ones
MemoryLogStorageHandlers = MemoryLogStorageHandler
MentalNoteStorageHandlers = MentalNoteStorageHandler
ConversationStorageHandlers = ConversationStorageHandler

__all__ = [
    # New names (preferred)
    'MemoryLogStorageHandler',
    'MentalNoteStorageHandler',
    'ConversationStorageHandler',

    # Backward compatibility aliases
    'MemoryLogStorageHandlers',
    'MentalNoteStorageHandlers',
    'ConversationStorageHandlers',
]
