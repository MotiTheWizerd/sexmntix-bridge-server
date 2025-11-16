"""
Internal event handlers for memory log and mental note storage.

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
"""

from .handlers.memory_log_handler import MemoryLogStorageHandler
from .handlers.mental_note_handler import MentalNoteStorageHandler

# Backward compatibility aliases for existing code
# This allows gradual migration from old class names to new ones
MemoryLogStorageHandlers = MemoryLogStorageHandler
MentalNoteStorageHandlers = MentalNoteStorageHandler

__all__ = [
    # New names (preferred)
    'MemoryLogStorageHandler',
    'MentalNoteStorageHandler',

    # Backward compatibility aliases
    'MemoryLogStorageHandlers',
    'MentalNoteStorageHandlers',
]
