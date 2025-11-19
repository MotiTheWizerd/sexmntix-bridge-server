"""Configuration for SXThalamus module"""

from dataclasses import dataclass
import os


@dataclass
class SXThalamusConfig:
    """Configuration for SXThalamus service

    Note: Model configuration is now per-user in the database.
    GEMINI_API_KEY is loaded from environment via load_dotenv() in the client.
    """

    enabled: bool = True
    """Enable/disable SXThalamus preprocessing"""

    timeout_seconds: float = 30.0
    """Timeout for API calls in seconds"""

    max_retries: int = 2
    """Maximum retry attempts for failed API calls"""

    @classmethod
    def from_env(cls) -> "SXThalamusConfig":
        """
        Load configuration from environment variables.

        Environment variables:
            SXTHALAMUS_ENABLED: Enable/disable the service (default: true)
            GEMINI_API_KEY: Google Gemini API key (loaded in client via load_dotenv)
            SXTHALAMUS_TIMEOUT: Timeout in seconds (default: 30.0)
            SXTHALAMUS_MAX_RETRIES: Max retry attempts (default: 2)

        Returns:
            SXThalamusConfig instance with values from environment
        """
        return cls(
            enabled=os.getenv("SXTHALAMUS_ENABLED", "true").lower() == "true",
            timeout_seconds=float(os.getenv("SXTHALAMUS_TIMEOUT", "30.0")),
            max_retries=int(os.getenv("SXTHALAMUS_MAX_RETRIES", "2"))
        )
