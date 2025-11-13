"""
Batch Processor

Single Responsibility: Process multiple embedding requests concurrently with rate limiting.

This component handles concurrent processing of batch embedding requests,
with configurable batch sizes to avoid rate limits.
"""

import asyncio
from typing import List, Callable
from src.modules.embeddings.exceptions import ProviderError


class BatchProcessor:
    """
    Processes embedding requests in batches with rate limiting.

    Handles concurrent processing while respecting API rate limits.
    """

    def __init__(
        self,
        batch_size: int = 10,
        provider_name: str = "google"
    ):
        """
        Initialize batch processor.

        Args:
            batch_size: Number of requests to process concurrently
            provider_name: Provider name for error messages
        """
        self.batch_size = batch_size
        self.provider_name = provider_name

    async def process_batch(
        self,
        texts: List[str],
        embedding_func: Callable[[str], List[float]]
    ) -> List[List[float]]:
        """
        Process multiple texts in batches.

        Args:
            texts: List of texts to embed
            embedding_func: Async function to generate single embedding

        Returns:
            List of embedding vectors

        Raises:
            ProviderError: If any embedding generation fails
        """
        results = []

        # Process texts in batches to avoid rate limits
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]

            # Process batch concurrently
            batch_embeddings = await asyncio.gather(
                *[embedding_func(text) for text in batch],
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

    def calculate_batches(self, total_items: int) -> int:
        """
        Calculate number of batches needed.

        Args:
            total_items: Total number of items to process

        Returns:
            Number of batches
        """
        return (total_items + self.batch_size - 1) // self.batch_size
