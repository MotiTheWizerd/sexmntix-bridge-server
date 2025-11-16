"""
Logging message formatters for embedding service.

Provides consistent log message formatting across all embedding
service operations.
"""

from .config import EmbeddingServiceConfig


class EmbeddingLogFormatter:
    """Formats log messages for embedding service"""

    @staticmethod
    def format_initialization(provider_name: str, cache_enabled: bool) -> str:
        """
        Format service initialization message.

        Args:
            provider_name: Name of the embedding provider
            cache_enabled: Whether caching is enabled

        Returns:
            Formatted log message
        """
        return (
            f"EmbeddingService initialized with provider: {provider_name}, "
            f"cache_enabled: {cache_enabled}"
        )

    @staticmethod
    def format_cache_hit(text_preview: str) -> str:
        """
        Format cache hit message.

        Args:
            text_preview: Preview of the text (first N characters)

        Returns:
            Formatted log message
        """
        return f"Cache hit for text: {text_preview}..."

    @staticmethod
    def format_generation_started(text_preview: str) -> str:
        """
        Format embedding generation started message.

        Args:
            text_preview: Preview of the text

        Returns:
            Formatted log message
        """
        return f"Generating embedding for text: {text_preview}..."

    @staticmethod
    def format_generation_success(duration: float, dimensions: int) -> str:
        """
        Format successful generation message.

        Args:
            duration: Generation duration in seconds
            dimensions: Embedding vector dimensions

        Returns:
            Formatted log message
        """
        return (
            f"Embedding generated successfully in {duration:.2f}s, "
            f"dimensions: {dimensions}"
        )

    @staticmethod
    def format_generation_error(error: str) -> str:
        """
        Format generation error message.

        Args:
            error: Error message

        Returns:
            Formatted log message
        """
        return f"Failed to generate embedding: {error}"

    @staticmethod
    def format_batch_processing(count: int) -> str:
        """
        Format batch processing started message.

        Args:
            count: Number of texts in batch

        Returns:
            Formatted log message
        """
        return f"Processing batch of {count} texts"

    @staticmethod
    def format_batch_complete(
        total: int,
        cache_hits: int,
        duration: float
    ) -> str:
        """
        Format batch processing complete message.

        Args:
            total: Total number of embeddings
            cache_hits: Number of cache hits
            duration: Processing duration in seconds

        Returns:
            Formatted log message
        """
        return (
            f"Batch processing complete: {total} embeddings, "
            f"{cache_hits} cache hits, {duration:.2f}s"
        )

    @staticmethod
    def format_batch_error(error: str) -> str:
        """
        Format batch processing error message.

        Args:
            error: Error message

        Returns:
            Formatted log message
        """
        return f"Batch embedding generation failed: {error}"

    @staticmethod
    def format_health_check() -> str:
        """
        Format health check message.

        Returns:
            Formatted log message
        """
        return "Running provider health check"

    @staticmethod
    def format_cache_cleared() -> str:
        """
        Format cache cleared message.

        Returns:
            Formatted log message
        """
        return "Embedding cache cleared"

    @staticmethod
    def format_service_closed() -> str:
        """
        Format service closed message.

        Returns:
            Formatted log message
        """
        return "EmbeddingService closed"
