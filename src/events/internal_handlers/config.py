"""
Configuration and constants for internal event handlers.

Centralizes all configuration values, event names, and constants
used across the internal handlers module.
"""


class InternalHandlerConfig:
    """Configuration for internal event handlers"""

    # Event names that handlers subscribe to
    MEMORY_LOG_STORED_EVENT = "memory_log.stored"
    MENTAL_NOTE_STORED_EVENT = "mental_note.stored"

    # Logging prefixes for different handler types
    MEMORY_LOG_PREFIX = "[EVENT_HANDLER]"
    MENTAL_NOTE_PREFIX = "[MENTAL_NOTE_HANDLER]"

    # Content preview length for debugging
    CONTENT_PREVIEW_LENGTH = 100

    # Processing behavior flags
    ENABLE_POSTGRES_UPDATE = True
    NON_BLOCKING_FAILURES = True

    # Field names for event data extraction
    USER_ID_FIELD = "user_id"
    PROJECT_ID_FIELD = "project_id"
    MEMORY_LOG_ID_FIELD = "memory_log_id"
    MENTAL_NOTE_ID_FIELD = "mental_note_id"
    RAW_DATA_FIELD = "raw_data"
    CONTENT_FIELD = "content"

    # Messages
    NO_CONTENT_PLACEHOLDER = "NO CONTENT"

    @classmethod
    def get_event_names(cls):
        """Get all event names this module handles"""
        return [
            cls.MEMORY_LOG_STORED_EVENT,
            cls.MENTAL_NOTE_STORED_EVENT
        ]
