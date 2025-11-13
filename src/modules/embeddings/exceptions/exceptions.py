"""
Custom exceptions for the embeddings module.
"""


class EmbeddingError(Exception):
    """Base exception for all embedding-related errors."""

    pass


class ProviderError(EmbeddingError):
    """Raised when an embedding provider encounters an error."""

    def __init__(self, provider_name: str, message: str, original_error: Exception | None = None):
        self.provider_name = provider_name
        self.original_error = original_error
        super().__init__(f"[{provider_name}] {message}")


class APIRateLimitError(ProviderError):
    """Raised when API rate limits are exceeded."""

    def __init__(self, provider_name: str, retry_after: int | None = None):
        self.retry_after = retry_after
        message = f"Rate limit exceeded"
        if retry_after:
            message += f". Retry after {retry_after} seconds"
        super().__init__(provider_name, message)


class InvalidTextError(EmbeddingError):
    """Raised when input text is invalid or empty."""

    def __init__(self, reason: str):
        super().__init__(f"Invalid text input: {reason}")


class ProviderConnectionError(ProviderError):
    """Raised when unable to connect to embedding provider."""

    def __init__(self, provider_name: str, original_error: Exception):
        super().__init__(
            provider_name,
            f"Connection failed: {str(original_error)}",
            original_error
        )


class ProviderTimeoutError(ProviderError):
    """Raised when embedding provider request times out."""

    def __init__(self, provider_name: str, timeout_seconds: float):
        super().__init__(
            provider_name,
            f"Request timed out after {timeout_seconds} seconds"
        )
