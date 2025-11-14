"""
ChromaDB Configuration

Centralized configuration for ChromaDB client settings and constants.
"""

from dataclasses import dataclass


@dataclass
class ChromaDBConfig:
    """Configuration for ChromaDB client."""

    # Telemetry settings
    anonymized_telemetry: bool = False
    """Disable ChromaDB anonymous telemetry"""

    allow_reset: bool = True
    """Allow reset of entire ChromaDB instance"""

    # Collection naming
    default_collection_prefix: str = "semantix"
    """Default prefix for collection names"""

    hash_length: int = 16
    """Length of hash suffix for collection names (ChromaDB supports 3-63 chars)"""

    # Constraints
    min_collection_name_length: int = 3
    """Minimum collection name length (ChromaDB requirement)"""

    max_collection_name_length: int = 63
    """Maximum collection name length (ChromaDB requirement)"""

    def __post_init__(self):
        """Validate configuration."""
        if self.hash_length > self.max_collection_name_length - len(self.default_collection_prefix) - 1:
            raise ValueError(
                f"hash_length {self.hash_length} too large for max_collection_name_length {self.max_collection_name_length}"
            )


# Default configuration instance
DEFAULT_CONFIG = ChromaDBConfig()
