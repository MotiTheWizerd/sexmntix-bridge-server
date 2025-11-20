
import sys
import os
import asyncio

# Add project root to path
sys.path.append(os.getcwd())

from src.modules.core import EventBus, Logger
from src.modules.embeddings.service import EmbeddingService
from src.modules.embeddings.providers import BaseEmbeddingProvider
from src.modules.embeddings.models import EmbeddingResponse, ProviderHealthResponse

# Mock Provider
class MockProvider(BaseEmbeddingProvider):
    def __init__(self):
        self.provider_name = "mock"
        self.config = type('obj', (object,), {'model_name': 'test-model'})
    
    async def generate_embedding(self, text: str):
        return [0.1, 0.2, 0.3]

    async def generate_embeddings_batch(self, texts):
        return [[0.1] * 3 for _ in texts]

    async def health_check(self):
        return True

async def main():
    print("Initializing dependencies...")
    event_bus = EventBus()
    logger = Logger("test")
    provider = MockProvider()
    
    print("Initializing EmbeddingService...")
    service = EmbeddingService(event_bus, logger, provider, cache_enabled=False)
    
    print("Testing generate_embedding...")
    resp = await service.generate_embedding("hello world")
    print(f"Response: {resp}")
    
    print("Testing batch...")
    batch_resp = await service.generate_embeddings_batch(["a", "b"])
    print(f"Batch Response: {batch_resp}")
    
    print("Testing health check...")
    health = await service.health_check()
    print(f"Health: {health}")
    
    print("SUCCESS")

if __name__ == "__main__":
    asyncio.run(main())
