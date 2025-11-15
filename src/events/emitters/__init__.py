"""
Event emitters - Helper classes to emit events from business logic

This package provides domain-specific emitters for different event types.
The EventEmitter class provides a unified interface for backward compatibility.

Usage:
    # Use the unified EventEmitter (recommended for backward compatibility)
    from src.events.emitters import EventEmitter
    emitter = EventEmitter(socket_service)
    await emitter.emit_memory_log_created(memory_log)

    # Or use domain-specific emitters directly (for new code)
    from src.events.emitters import MemoryLogEmitter
    memory_emitter = MemoryLogEmitter(socket_service)
    await memory_emitter.emit_memory_log_created(memory_log)
"""
from .base import BaseEmitter
from .memory_log_emitters import MemoryLogEmitter
from .mental_note_emitters import MentalNoteEmitter
from .user_emitters import UserEmitter


class EventEmitter(MemoryLogEmitter, MentalNoteEmitter, UserEmitter):
    """
    Unified event emitter with all domain-specific emitters.

    This class combines all domain emitters into a single interface
    for convenience and backward compatibility. It provides access to:
    - Memory log events (emit_memory_log_*)
    - Mental note events (emit_mental_note_*)
    - User status events (emit_user_status_*)

    For new code, consider using domain-specific emitters directly:
    - MemoryLogEmitter
    - MentalNoteEmitter
    - UserEmitter

    Example:
        emitter = EventEmitter(socket_service)
        await emitter.emit_memory_log_created(memory_log)
        await emitter.emit_mental_note_created(mental_note)
        await emitter.emit_user_status_changed(user_id, status)
    """
    pass


__all__ = [
    'BaseEmitter',
    'EventEmitter',
    'MemoryLogEmitter',
    'MentalNoteEmitter',
    'UserEmitter',
]
