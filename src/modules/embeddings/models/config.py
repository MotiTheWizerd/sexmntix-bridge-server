"""
Configuration models for embedding providers.
"""

from pydantic import BaseModel
from typing import Literal, Optional


class ProviderConfig(BaseModel):
    """Configuration for embedding providers."""

    provider_name: Literal["google", "openai", "local"] = "google"
    model_name: str = "models/text-embedding-004"
    api_key: Optional[str] = None
    timeout_seconds: float = 30.0
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
