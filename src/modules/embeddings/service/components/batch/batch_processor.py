"""
Batch processor component.

Responsible for batch processing logic (cache check → generate → store).
"""

from typing import List, Tuple
from ....providers import BaseEmbeddingProvider
from ....models import EmbeddingResponse
from ..cache.cache_handler import CacheHandler
from ..responses.response_builder import ResponseBuilder


class BatchProcessor:
    """
    Processes batch embedding requests with cache optimization.
    
    Single responsibility: Coordinate batch processing workflow.
    """
    
    async def process_batch(
        self,
        texts: List[str],
        model: str,
        provider: BaseEmbeddingProvider,
        cache_handler: CacheHandler,
        response_builder: ResponseBuilder
    ) -> Tuple[List[EmbeddingResponse], int]:
        """
        Process batch of texts with cache optimization.
        
        Workflow:
        1. Check cache for each text
        2. Generate embeddings for cache misses
        3. Store newly generated embeddings
        4. Return all responses with cache hit count
        
        Args:
            texts: List of texts to embed
            model: Model name to use
            provider: Embedding provider
            cache_handler: Cache handler for get/store operations
            response_builder: Response builder for creating responses
            
        Returns:
            Tuple of (list of responses, cache hit count)
        """
        responses = []
        cache_hits = 0
        texts_to_generate = []
        
        # Phase 1: Check cache for all texts
        for text in texts:
            cached_embedding = cache_handler.get_embedding(text, model)
            if cached_embedding:
                cache_hits += 1
                responses.append(
                    response_builder.build_embedding_response(
                        text=text,
                        embedding=cached_embedding,
                        model=model,
                        cached=True
                    )
                )
            else:
                texts_to_generate.append(text)
        
        # Phase 2: Generate missing embeddings
        if texts_to_generate:
            generated_embeddings = await provider.generate_embeddings_batch(texts_to_generate)
            
            # Phase 3: Store and build responses for newly generated
            for text, embedding in zip(texts_to_generate, generated_embeddings):
                cache_handler.store_embedding(text, model, embedding)
                responses.append(
                    response_builder.build_embedding_response(
                        text=text,
                        embedding=embedding,
                        model=model,
                        cached=False
                    )
                )
        
        return responses, cache_hits
