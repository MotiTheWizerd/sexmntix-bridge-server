"""
Batch processing for embedding service.

Handles batch embedding generation with cache optimization.
"""

from typing import List, Tuple
from ...providers import BaseEmbeddingProvider
from ...models import EmbeddingResponse
from .cache_handler import CacheHandler
from .response_builder import ResponseBuilder


class BatchProcessor:
    """Processes batch embedding requests with cache optimization"""

    def __init__(
        self,
        cache_handler: CacheHandler,
        provider: BaseEmbeddingProvider,
        response_builder: ResponseBuilder
    ):
        """
        Initialize batch processor.

        Args:
            cache_handler: Cache handler for checking and storing embeddings
            provider: Embedding provider for generation
            response_builder: Response builder for creating response objects
        """
        self.cache_handler = cache_handler
        self.provider = provider
        self.response_builder = response_builder

    async def process_batch(
        self,
        texts: List[str],
        model: str
    ) -> Tuple[List[EmbeddingResponse], int]:
        """
        Process batch of texts with cache optimization.

        Args:
            texts: List of texts to embed
            model: Model name

        Returns:
            Tuple of (list of responses, cache hit count)
        """
        embeddings_responses = []
        cache_hits = 0

        # Identify texts that need generation
        texts_to_generate = []
        text_indices = []

        for idx, text in enumerate(texts):
            # Check cache
            cached = self.cache_handler.get_cached_embedding(text, model)
            if cached:
                cache_hits += 1
                response = self.response_builder.build_embedding_response(
                    text=text,
                    embedding=cached,
                    model=model,
                    provider=self.provider.provider_name,
                    cached=True
                )
                embeddings_responses.append(response)
                continue

            # Not in cache - need to generate
            texts_to_generate.append(text)
            text_indices.append(idx)

        # Generate embeddings for uncached texts
        if texts_to_generate:
            generated_embeddings = await self._generate_uncached_embeddings(
                texts_to_generate,
                model
            )

            # Create responses and cache
            for text, embedding in zip(texts_to_generate, generated_embeddings):
                self.cache_handler.store_embedding(text, model, embedding)

                response = self.response_builder.build_embedding_response(
                    text=text,
                    embedding=embedding,
                    model=model,
                    provider=self.provider.provider_name,
                    cached=False
                )
                embeddings_responses.append(response)

        return embeddings_responses, cache_hits

    async def _generate_uncached_embeddings(
        self,
        texts: List[str],
        model: str
    ) -> List[List[float]]:
        """
        Generate embeddings for uncached texts.

        Args:
            texts: List of texts to generate embeddings for
            model: Model name

        Returns:
            List of embedding vectors

        Raises:
            ProviderError: If generation fails
        """
        return await self.provider.generate_embeddings_batch(texts)
