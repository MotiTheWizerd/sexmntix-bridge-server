"""
Application-level configuration.

Loads app metadata, database, and CORS settings from environment.
"""

import os
from dataclasses import dataclass


@dataclass
class AppConfig:
    """Application configuration loaded from environment variables."""

    # Database (required field - must come first)
    database_url: str

    # App metadata
    title: str = "Semantic Bridge Server"
    description: str = "Event-driven API server"
    version: str = "0.1.0"

    # CORS settings
    cors_allow_origins: list[str] = None
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = None
    cors_allow_headers: list[str] = None

    def __post_init__(self):
        """Set default CORS values if not provided."""
        if self.cors_allow_origins is None:
            self.cors_allow_origins = ["*"]
        if self.cors_allow_methods is None:
            self.cors_allow_methods = ["*"]
        if self.cors_allow_headers is None:
            self.cors_allow_headers = ["*"]


def load_app_config() -> AppConfig:
    """Load application configuration from environment.

    Returns:
        AppConfig instance with settings loaded from environment
    """
    return AppConfig(
        database_url=os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://user:password@localhost:5432/semantic_bridge"
        )
    )
