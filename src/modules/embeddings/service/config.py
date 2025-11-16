"""
Configuration and constants for embedding service.

Centralizes all configuration values, event names, and constants
used across the embedding service module.
"""


class EmbeddingServiceConfig:
    """Configuration for embedding service"""

    # Event names that the service publishes
    CACHE_HIT_EVENT = "embedding.cache_hit"
    GENERATED_EVENT = "embedding.generated"
    ERROR_EVENT = "embedding.error"
    BATCH_GENERATED_EVENT = "embedding.batch_generated"
    HEALTH_CHECK_EVENT = "embedding.health_check"

    # Text preview lengths for logging and events
    TEXT_PREVIEW_SHORT = 50
    TEXT_PREVIEW_LONG = 100

    # Timing precision
    DURATION_PRECISION_SECONDS = 2
    DURATION_PRECISION_MS = 2
    BATCH_TIME_PRECISION = 3

    # Validation
    MIN_TEXT_LENGTH = 1

    @classmethod
    def get_event_names(cls):
        """Get all event names this service publishes"""
        return [
            cls.CACHE_HIT_EVENT,
            cls.GENERATED_EVENT,
            cls.ERROR_EVENT,
            cls.BATCH_GENERATED_EVENT,
            cls.HEALTH_CHECK_EVENT
        ]
