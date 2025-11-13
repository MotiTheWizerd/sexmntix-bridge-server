"""
Google API Client

Single Responsibility: Manage HTTP client lifecycle for Google API interactions.

This component handles the initialization, configuration, and lifecycle management
of the async HTTP client used to communicate with Google's embedding API.
"""

import httpx


class GoogleAPIClient:
    """
    Manages HTTP client for Google Generative AI API.

    Handles client initialization, configuration, and cleanup.
    """

    def __init__(self, api_key: str, timeout_seconds: float = 30.0):
        """
        Initialize Google API client.

        Args:
            api_key: Google API key for authentication
            timeout_seconds: Request timeout in seconds
        """
        self.api_key = api_key
        self.timeout = timeout_seconds

        # Initialize async HTTP client
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            headers={"x-goog-api-key": self.api_key}
        )

    def get_client(self) -> httpx.AsyncClient:
        """
        Get the configured HTTP client.

        Returns:
            Configured httpx.AsyncClient instance
        """
        return self.client

    async def close(self):
        """Close the HTTP client and release resources."""
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
