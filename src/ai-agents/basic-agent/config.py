"""Configuration for BasicAgent module"""

from dataclasses import dataclass
import os


@dataclass
class BasicAgentConfig:
    """Configuration for BasicAgent service

    Note: GEMINI_API_KEY is loaded from environment via load_dotenv() in the client
    """

    enabled: bool = True
    """Enable/disable BasicAgent"""

    model: str = "gemini-2.0-flash"
    """Gemini model identifier"""

    timeout_seconds: float = 30.0
    """Timeout for API calls in seconds"""

    max_retries: int = 2
    """Maximum retry attempts for failed API calls"""

    @classmethod
    def from_env(cls) -> "BasicAgentConfig":
        """
        Load configuration from environment variables.

        Environment variables:
            BASIC_AGENT_ENABLED: Enable/disable the service (default: true)
            GEMINI_API_KEY: Google Gemini API key (loaded in client via load_dotenv)
            BASIC_AGENT_MODEL: Model identifier (default: gemini-2.0-flash)
            BASIC_AGENT_TIMEOUT: Timeout in seconds (default: 30.0)
            BASIC_AGENT_MAX_RETRIES: Max retry attempts (default: 2)

        Returns:
            BasicAgentConfig instance with values from environment
        """
        return cls(
            enabled=os.getenv("BASIC_AGENT_ENABLED", "true").lower() == "true",
            model=os.getenv("BASIC_AGENT_MODEL", "gemini-2.0-flash"),
            timeout_seconds=float(os.getenv("BASIC_AGENT_TIMEOUT", "30.0")),
            max_retries=int(os.getenv("BASIC_AGENT_MAX_RETRIES", "2"))
        )
