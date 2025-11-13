"""
Base Embedding Provider

Single Responsibility: Define the interface contract for all embedding providers.

This abstract base class establishes the common interface that all embedding
providers must implement.
"""

from abc import ABC, abstractmethod
from typing import List
from src.modules.embeddings.models import ProviderConfig


class BaseEmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""

    def __init__(self, config: ProviderConfig):
        """
        Initialize the provider with configuration.

        Args:
            config: Provider configuration including API keys, timeouts, etc.
        """
        self.config = config
        self.provider_name = config.provider_name

    @abstractmethod
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for a single text.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector

        Raises:
            ProviderError: If embedding generation fails
        """
        pass

    @abstractmethod
    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embedding vectors for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors

        Raises:
            ProviderError: If batch embedding generation fails
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the provider is healthy and accessible.

        Returns:
            True if healthy, False otherwise
        """
        pass
