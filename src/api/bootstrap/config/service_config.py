"""
Service-level configuration.

Loads configuration for embedding service, ChromaDB, and background tasks.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class EmbeddingConfig:
    """Configuration for embedding service."""

    api_key: Optional[str] = None
    provider_name: str = "google"
    model_name: str = "models/text-embedding-004"
    timeout_seconds: float = 30.0
    max_retries: int = 3
    cache_size: int = 1000
    cache_ttl_hours: int = 24
    cache_enabled: bool = True

    def __post_init__(self):
        """Load configuration from environment."""
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.model_name = os.getenv("EMBEDDING_MODEL", self.model_name)
        self.timeout_seconds = float(os.getenv("EMBEDDING_TIMEOUT", str(self.timeout_seconds)))
        self.max_retries = int(os.getenv("EMBEDDING_MAX_RETRIES", str(self.max_retries)))
        self.cache_size = int(os.getenv("EMBEDDING_CACHE_SIZE", str(self.cache_size)))
        self.cache_ttl_hours = int(os.getenv("EMBEDDING_CACHE_TTL_HOURS", str(self.cache_ttl_hours)))
        self.cache_enabled = os.getenv("EMBEDDING_CACHE_ENABLED", "true").lower() == "true"

    @property
    def is_available(self) -> bool:
        """Check if embedding service can be initialized."""
        return self.api_key is not None


@dataclass
class ChromaDBConfig:
    """Configuration for ChromaDB."""

    base_path: str = "./data/chromadb"

    def __post_init__(self):
        """Load configuration from environment."""
        self.base_path = os.getenv("CHROMADB_PATH", self.base_path)


@dataclass
class BackgroundTaskConfig:
    """Configuration for background tasks."""

    metrics_interval_seconds: int = 5

    def __post_init__(self):
        """Load configuration from environment."""
        self.metrics_interval_seconds = int(
            os.getenv("METRICS_INTERVAL_SECONDS", str(self.metrics_interval_seconds))
        )


@dataclass
class ServiceConfig:
    """Combined service configuration."""

    embedding: EmbeddingConfig
    chromadb: ChromaDBConfig
    background_tasks: BackgroundTaskConfig

    def __init__(self):
        """Initialize all service configs."""
        self.embedding = EmbeddingConfig()
        self.chromadb = ChromaDBConfig()
        self.background_tasks = BackgroundTaskConfig()


def load_service_config() -> ServiceConfig:
    """Load service configuration from environment.

    Returns:
        ServiceConfig instance with all service settings
    """
    return ServiceConfig()
