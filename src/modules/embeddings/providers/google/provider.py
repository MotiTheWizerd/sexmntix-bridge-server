"""
Google Embedding Provider

Single Responsibility: Orchestrate Google embedding operations using specialized components.

This provider composes various single-responsibility components to implement
the embedding provider interface for Google Generative AI.
"""

from typing import List
import httpx
from src.modules.embeddings.models import ProviderConfig
from src.modules.embeddings.providers.base import BaseEmbeddingProvider
from src.modules.embeddings.providers.google.client import GoogleAPIClient
from src.modules.embeddings.providers.google.request_builder import GoogleRequestBuilder
from src.modules.embeddings.providers.google.response_parser import GoogleResponseParser
from src.modules.embeddings.providers.google.retry_handler import RetryHandler
from src.modules.embeddings.providers.google.batch_processor import BatchProcessor


class GoogleEmbeddingProvider(BaseEmbeddingProvider):
    """
    Google Generative AI embedding provider.

    Orchestrates specialized components:
    - GoogleAPIClient: HTTP client management
    - GoogleRequestBuilder: Request payload construction
    - GoogleResponseParser: Response parsing and error handling
    - RetryHandler: Retry logic with exponential backoff
    - BatchProcessor: Concurrent batch processing with rate limiting

    Uses the Gemini `gemini-embedding-001` model by default.
    """

    def __init__(self, config: ProviderConfig):
        """
        Initialize Google embedding provider with component composition.

        Args:
            config: Provider configuration with Google API key

        Raises:
            ValueError: If Google API key is not provided
        """
        super().__init__(config)

        if not config.api_key:
            raise ValueError("Google/Gemini API key is required")

        self.api_key = config.api_key
        self.model = config.model_name or "models/gemini-embedding-001"
        self.timeout = config.timeout_seconds

        # Initialize components
        self.api_client = GoogleAPIClient(
            api_key=self.api_key,
            timeout_seconds=self.timeout
        )

        self.request_builder = GoogleRequestBuilder(
            model_name=self.model
        )

        self.response_parser = GoogleResponseParser(
            provider_name=self.provider_name
        )

        self.retry_handler = RetryHandler(
            max_retries=config.max_retries,
            retry_delay_seconds=config.retry_delay_seconds,
            provider_name=self.provider_name
        )

        self.batch_processor = BatchProcessor(
            batch_size=10,  # Process 10 concurrent requests at a time
            provider_name=self.provider_name
        )

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding using Google's Gemini embedding endpoint.

        Delegates to specialized components for HTTP requests, retries,
        and response parsing.

        Args:
            text: Text to embed

        Returns:
            Vector embedding as list of floats

        Raises:
            ProviderError: If API call fails
            APIRateLimitError: If rate limit is exceeded
            ProviderTimeoutError: If request times out
            ProviderConnectionError: If connection fails
        """
        async def make_request() -> List[float]:
            """Inner function to make the actual API request."""
            url = self.request_builder.build_embedding_url()
            payload = self.request_builder.build_embedding_payload(text)

            client = self.api_client.get_client()
            response = await client.post(url, json=payload)

            return self.response_parser.parse_embedding_response(response)

        # Error handler for retry logic
        def handle_error(exception: Exception, attempt: int, is_final: bool):
            self.response_parser.handle_http_exception(
                exception=exception,
                timeout=self.timeout,
                is_final_attempt=is_final
            )

        # Execute with retry logic
        return await self.retry_handler.execute_with_retry(
            operation=make_request,
            error_handler=handle_error
        )

    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Delegates to BatchProcessor for concurrent processing with rate limiting.

        Note: Google API doesn't have a native batch endpoint,
        so we process texts concurrently with rate limiting.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors

        Raises:
            ProviderError: If any embedding generation fails
        """
        return await self.batch_processor.process_batch(
            texts=texts,
            embedding_func=self.generate_embedding
        )

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
        """Close the HTTP client and release resources."""
        await self.api_client.close()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
