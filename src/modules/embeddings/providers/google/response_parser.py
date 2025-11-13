"""
Google Response Parser

Single Responsibility: Parse and validate Google API responses.

This component handles parsing response payloads, extracting embeddings,
and mapping HTTP errors to appropriate exceptions.
"""

from typing import List
import httpx
from src.modules.embeddings.exceptions import (
    ProviderError,
    APIRateLimitError,
)


class GoogleResponseParser:
    """
    Parses responses from Google Generative AI embedding API.

    Handles response validation, error mapping, and data extraction.
    """

    def __init__(self, provider_name: str = "google"):
        """
        Initialize response parser.

        Args:
            provider_name: Provider name for error messages
        """
        self.provider_name = provider_name

    def parse_embedding_response(self, response: httpx.Response) -> List[float]:
        """
        Parse embedding from API response.

        Args:
            response: HTTP response from Google API

        Returns:
            Embedding vector as list of floats

        Raises:
            APIRateLimitError: If rate limit exceeded
            ProviderError: If response is invalid or contains errors
        """
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

        # Parse JSON response
        data = response.json()

        # Validate response structure
        if "embedding" not in data or "values" not in data["embedding"]:
            raise ProviderError(
                self.provider_name,
                f"Unexpected response format: {data}"
            )

        return data["embedding"]["values"]

    def handle_http_exception(
        self,
        exception: Exception,
        timeout: float,
        is_final_attempt: bool
    ) -> None:
        """
        Handle HTTP exceptions and raise appropriate provider errors.

        Args:
            exception: The caught exception
            timeout: Timeout value for context
            is_final_attempt: Whether this is the final retry attempt

        Raises:
            ProviderTimeoutError: If timeout occurred
            ProviderConnectionError: If connection failed
            ProviderError: For other HTTP errors
        """
        if not is_final_attempt:
            return  # Allow retry

        from src.modules.embeddings.exceptions import (
            ProviderTimeoutError,
            ProviderConnectionError,
        )

        if isinstance(exception, httpx.TimeoutException):
            raise ProviderTimeoutError(self.provider_name, timeout)
        elif isinstance(exception, httpx.ConnectError):
            raise ProviderConnectionError(self.provider_name, exception)
        elif isinstance(exception, (httpx.HTTPError, httpx.RequestError)):
            raise ProviderError(
                self.provider_name,
                f"HTTP error occurred: {str(exception)}",
                exception
            )
        else:
            raise ProviderError(
                self.provider_name,
                f"Unexpected error: {str(exception)}",
                exception
            )
