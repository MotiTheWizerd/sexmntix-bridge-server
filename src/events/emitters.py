"""
Event emitters - Compatibility shim

DEPRECATED: This file is kept for backward compatibility.
New code should import from src.events.emitters package directly.

Migration guide:
    Old: from src.events.emitters import EventEmitter
    New: from src.events.emitters import EventEmitter  # Still works!

    Or use domain-specific emitters:
    from src.events.emitters import MemoryLogEmitter, MentalNoteEmitter, UserEmitter
"""
# Re-export from the new package location
from .emitters import (
    BaseEmitter,
    EventEmitter,
    MemoryLogEmitter,
    MentalNoteEmitter,
    UserEmitter,
)

__all__ = [
    'BaseEmitter',
    'EventEmitter',
    'MemoryLogEmitter',
    'MentalNoteEmitter',
    'UserEmitter',
]
