"""
Vector Storage Configuration

Centralized configuration for vector storage service settings and defaults.
"""

from dataclasses import dataclass


@dataclass
class VectorStorageConfig:
    """Configuration for vector storage service."""

    # Search defaults
    default_search_limit: int = 10
    """Default number of search results to return"""

    default_min_similarity: float = 0.0
    """Default minimum similarity threshold (0.0 to 1.0)"""

    # Temporal decay defaults
    default_enable_temporal_decay: bool = False
    """Enable temporal decay scoring by default"""

    default_half_life_days: float = 30.0
    """Half-life in days for exponential decay (default: 30 days)"""

    # Embedding defaults
    default_collection_prefix: str = "semantix"
    """Default prefix for collection names"""

    # Storage defaults
    batch_size: int = 100
    """Batch size for bulk storage operations"""

    def __post_init__(self):
        """Validate configuration."""
        if not (0.0 <= self.default_min_similarity <= 1.0):
            raise ValueError(
                f"default_min_similarity must be between 0.0 and 1.0, got {self.default_min_similarity}"
            )

        if self.default_half_life_days <= 0:
            raise ValueError(
                f"default_half_life_days must be positive, got {self.default_half_life_days}"
            )

        if self.default_search_limit < 1:
            raise ValueError(
                f"default_search_limit must be at least 1, got {self.default_search_limit}"
            )

        if self.batch_size < 1:
            raise ValueError(f"batch_size must be at least 1, got {self.batch_size}")


# Default configuration instance
DEFAULT_CONFIG = VectorStorageConfig()
