"""
Embedding provider abstraction and implementations.
"""

from abc import ABC, abstractmethod
from typing import List
import httpx
import asyncio
from .models import ProviderConfig
from .exceptions import (
    ProviderError,
    APIRateLimitError,
    ProviderConnectionError,
    ProviderTimeoutError,
)


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


class GoogleEmbeddingProvider(BaseEmbeddingProvider):
    """
    Google Generative AI embedding provider.
    Uses the text-embedding-004 model.
    """

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

    def __init__(self, config: ProviderConfig):
        """
        Initialize Google embedding provider.

        Args:
            config: Provider configuration with Google API key
        """
        super().__init__(config)

        if not config.api_key:
            raise ValueError("Google API key is required")

        self.api_key = config.api_key
        self.model = config.model_name or "models/text-embedding-004"
        self.timeout = config.timeout_seconds
        self.max_retries = config.max_retries
        self.retry_delay = config.retry_delay_seconds

        # Initialize async HTTP client
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            headers={"x-goog-api-key": self.api_key}
        )

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding using Google's text-embedding-004 model.

        Args:
            text: Text to embed

        Returns:
            Vector embedding as list of floats

        Raises:
            ProviderError: If API call fails
            APIRateLimitError: If rate limit is exceeded
            ProviderTimeoutError: If request times out
        """
        url = f"{self.BASE_URL}/{self.model}:embedContent"

        payload = {
            "model": self.model,
            "content": {
                "parts": [{"text": text}]
            }
        }

        # Retry logic with exponential backoff
        for attempt in range(self.max_retries):
            try:
                response = await self.client.post(url, json=payload)

                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    raise APIRateLimitError(self.provider_name, retry_after)

                # Handle other HTTP errors
                if response.status_code != 200:
                    error_detail = response.text
                    raise ProviderError(
                        self.provider_name,
                        f"API returned status {response.status_code}: {error_detail}"
                    )

                # Parse response
                data = response.json()

                if "embedding" not in data or "values" not in data["embedding"]:
                    raise ProviderError(
                        self.provider_name,
                        f"Unexpected response format: {data}"
                    )

                return data["embedding"]["values"]

            except httpx.TimeoutException as e:
                if attempt == self.max_retries - 1:
                    raise ProviderTimeoutError(self.provider_name, self.timeout)
                await asyncio.sleep(self.retry_delay * (2 ** attempt))

            except httpx.ConnectError as e:
                if attempt == self.max_retries - 1:
                    raise ProviderConnectionError(self.provider_name, e)
                await asyncio.sleep(self.retry_delay * (2 ** attempt))

            except (httpx.HTTPError, httpx.RequestError) as e:
                if attempt == self.max_retries - 1:
                    raise ProviderError(
                        self.provider_name,
                        f"HTTP error occurred: {str(e)}",
                        e
                    )
                await asyncio.sleep(self.retry_delay * (2 ** attempt))

        # Should never reach here due to raises in loop
        raise ProviderError(self.provider_name, "Max retries exceeded")

    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Note: Google API doesn't have a native batch endpoint,
        so we process texts concurrently with rate limiting.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        # Process texts concurrently (limited to 10 at a time to avoid rate limits)
        batch_size = 10
        results = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = await asyncio.gather(
                *[self.generate_embedding(text) for text in batch],
                return_exceptions=True
            )

            # Check for exceptions in results
            for idx, result in enumerate(batch_embeddings):
                if isinstance(result, Exception):
                    raise ProviderError(
                        self.provider_name,
                        f"Failed to embed text at index {i + idx}: {str(result)}",
                        result
                    )

            results.extend(batch_embeddings)

        return results

    async def health_check(self) -> bool:
        """
        Check if Google API is accessible.

        Returns:
            True if API is healthy, False otherwise
        """
        try:
            # Use a simple test embedding
            test_text = "health check"
            await self.generate_embedding(test_text)
            return True
        except Exception:
            return False

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
