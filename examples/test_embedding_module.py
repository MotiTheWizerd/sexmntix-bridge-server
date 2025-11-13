"""
Test script for the embedding module.

This demonstrates the embedding module functionality without requiring
a running FastAPI server.

Requirements:
1. Set GOOGLE_API_KEY in your .env file
2. Run: python examples/test_embedding_module.py
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.modules.core import EventBus, Logger
from src.modules.embeddings import (
    EmbeddingService,
    GoogleEmbeddingProvider,
    ProviderConfig,
    EmbeddingCache,
)


async def test_single_embedding():
    """Test generating a single embedding."""
    print("\n" + "=" * 60)
    print("TEST 1: Single Embedding Generation")
    print("=" * 60)

    # Initialize service
    event_bus = EventBus()
    logger = Logger("embedding-test")

    config = ProviderConfig(
        provider_name="google",
        model_name="models/text-embedding-004",
        api_key=os.getenv("GOOGLE_API_KEY"),
        timeout_seconds=30.0,
        max_retries=3
    )

    provider = GoogleEmbeddingProvider(config)
    cache = EmbeddingCache(max_size=100)
    service = EmbeddingService(
        event_bus=event_bus,
        logger=logger,
        provider=provider,
        cache=cache,
        cache_enabled=True
    )

    # Test text
    text = "permission dialog UI redesign with dark metallic theme"

    print(f"\nInput text: '{text}'")
    print("Generating embedding...")

    try:
        result = await service.generate_embedding(text)

        print(f"\nSuccess!")
        print(f"  Model: {result.model}")
        print(f"  Provider: {result.provider}")
        print(f"  Dimensions: {result.dimensions}")
        print(f"  Cached: {result.cached}")
        print(f"  Vector preview: [{result.embedding[0]:.4f}, {result.embedding[1]:.4f}, ...]")

        # Test cache hit
        print("\nTesting cache (re-embedding same text)...")
        result2 = await service.generate_embedding(text)

        print(f"  Cached: {result2.cached}")
        print(f"  Cache stats: {service.get_cache_stats()}")

    except Exception as e:
        print(f"\nError: {e}")
        print("\nMake sure GOOGLE_API_KEY is set in your .env file")

    finally:
        await service.close()


async def test_batch_embedding():
    """Test batch embedding generation."""
    print("\n" + "=" * 60)
    print("TEST 2: Batch Embedding Generation")
    print("=" * 60)

    # Initialize service
    event_bus = EventBus()
    logger = Logger("embedding-test")

    config = ProviderConfig(
        provider_name="google",
        api_key=os.getenv("GOOGLE_API_KEY")
    )

    provider = GoogleEmbeddingProvider(config)
    cache = EmbeddingCache()
    service = EmbeddingService(
        event_bus=event_bus,
        logger=logger,
        provider=provider,
        cache=cache
    )

    # Test texts
    texts = [
        "permission dialog UI redesign",
        "authentication flow improvements",
        "dark mode implementation",
        "streaming bug fixes"
    ]

    print(f"\nGenerating embeddings for {len(texts)} texts:")
    for i, text in enumerate(texts, 1):
        print(f"  {i}. {text}")

    try:
        result = await service.generate_embeddings_batch(texts)

        print(f"\nSuccess!")
        print(f"  Total embeddings: {result.total_count}")
        print(f"  Cache hits: {result.cache_hits}")
        print(f"  Processing time: {result.processing_time_seconds}s")

        print("\nEmbedding details:")
        for i, emb in enumerate(result.embeddings, 1):
            print(f"  {i}. Dimensions: {emb.dimensions}, Cached: {emb.cached}")

    except Exception as e:
        print(f"\nError: {e}")

    finally:
        await service.close()


async def test_health_check():
    """Test provider health check."""
    print("\n" + "=" * 60)
    print("TEST 3: Provider Health Check")
    print("=" * 60)

    event_bus = EventBus()
    logger = Logger("embedding-test")

    config = ProviderConfig(
        provider_name="google",
        api_key=os.getenv("GOOGLE_API_KEY")
    )

    provider = GoogleEmbeddingProvider(config)
    service = EmbeddingService(
        event_bus=event_bus,
        logger=logger,
        provider=provider
    )

    try:
        result = await service.health_check()

        print(f"\nProvider: {result.provider}")
        print(f"Status: {result.status}")
        print(f"Model: {result.model}")
        print(f"Latency: {result.latency_ms}ms" if result.latency_ms else "Unavailable")

    except Exception as e:
        print(f"\nError: {e}")

    finally:
        await service.close()


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("EMBEDDING MODULE TEST SUITE")
    print("=" * 60)

    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key or api_key == "your_google_api_key_here":
        print("\n❌ ERROR: GOOGLE_API_KEY not configured")
        print("\nPlease:")
        print("1. Get API key from: https://aistudio.google.com/app/apikey")
        print("2. Add to .env file: GOOGLE_API_KEY=your_actual_key")
        print("3. Run this script again")
        return

    print(f"\n✓ Google API key found: {api_key[:10]}...")

    await test_single_embedding()
    await test_batch_embedding()
    await test_health_check()

    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
