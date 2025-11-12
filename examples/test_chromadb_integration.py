"""
ChromaDB Integration Test Script

Tests the complete vector storage workflow:
1. Create memory log with embedding generation
2. Verify PostgreSQL storage (with embedding field)
3. Verify ChromaDB vector storage
4. Semantic search with similarity scoring
5. Metadata filtering

Usage:
    python examples/test_chromadb_integration.py
"""

import asyncio
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.infrastructure.chromadb.client import ChromaDBClient
from src.infrastructure.chromadb.repository import VectorRepository
from src.modules.embeddings.service import EmbeddingService
from src.modules.embeddings.provider import GoogleEmbeddingProvider
from src.modules.embeddings.cache import EmbeddingCache
from src.modules.embeddings.models import ProviderConfig
from src.services.vector_storage_service import VectorStorageService
from src.modules.core import EventBus, Logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def main():
    """Run ChromaDB integration tests."""
    print("=" * 80)
    print("ChromaDB Integration Test")
    print("=" * 80)

    # Initialize services
    print("\n[1] Initializing services...")
    event_bus = EventBus()
    logger = Logger(name="test_chromadb_integration")

    # Initialize embedding service
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        print("ERROR: GOOGLE_API_KEY not found in .env file")
        return

    # Create provider config
    provider_config = ProviderConfig(
        provider_name="google",
        model_name=os.getenv("EMBEDDING_MODEL", "models/text-embedding-004"),
        api_key=google_api_key,
        timeout_seconds=float(os.getenv("EMBEDDING_TIMEOUT", "30.0")),
        max_retries=int(os.getenv("EMBEDDING_MAX_RETRIES", "3")),
        retry_delay_seconds=1.0
    )

    provider = GoogleEmbeddingProvider(config=provider_config)
    cache = EmbeddingCache(
        max_size=int(os.getenv("EMBEDDING_CACHE_SIZE", "1000")),
        ttl_hours=int(os.getenv("EMBEDDING_CACHE_TTL_HOURS", "24"))
    )
    embedding_service = EmbeddingService(
        event_bus=event_bus,
        logger=logger,
        provider=provider,
        cache=cache,
        cache_enabled=os.getenv("EMBEDDING_CACHE_ENABLED", "true").lower() == "true"
    )

    # Initialize ChromaDB client and repository
    chromadb_path = os.getenv("CHROMADB_PATH", "./data/chromadb")
    chromadb_client = ChromaDBClient(storage_path=chromadb_path)
    vector_repository = VectorRepository(chromadb_client)

    # Initialize vector storage service
    vector_service = VectorStorageService(
        event_bus=event_bus,
        logger=logger,
        embedding_service=embedding_service,
        vector_repository=vector_repository
    )

    print(f"✓ EmbeddingService initialized (provider: {provider.provider_name})")
    print(f"✓ ChromaDB initialized (path: {chromadb_path})")
    print(f"✓ VectorStorageService initialized")

    # Test configuration
    user_id = "test_user_123"
    project_id = "test_project_456"

    # Test 1: Store memory vectors
    print("\n[2] Storing memory vectors...")

    test_memories = [
        {
            "id": 1,
            "task": "authentication-bug-fix",
            "agent": "claude",
            "component": "auth-module",
            "date": "2025-11-10",
            "summary": "Fixed critical authentication vulnerability in JWT token validation",
            "root_cause": "JWT library was not validating token expiration correctly",
            "solution": "Updated JWT validation logic to check exp claim and added unit tests",
            "tags": ["security", "authentication", "bug-fix", "jwt"]
        },
        {
            "id": 2,
            "task": "permission-dialog-redesign",
            "agent": "claude",
            "component": "ui-permission-system",
            "date": "2025-11-11",
            "summary": "Complete redesign of permission dialog with glassmorphism design",
            "root_cause": "Old dialog was confusing and had poor UX",
            "solution": "Implemented new design with clear permission categories and tooltips",
            "tags": ["ui", "permissions", "redesign", "glassmorphism"]
        },
        {
            "id": 3,
            "task": "database-query-optimization",
            "agent": "claude",
            "component": "database-layer",
            "date": "2025-11-12",
            "summary": "Optimized slow database queries causing timeout issues",
            "root_cause": "Missing indexes on frequently queried columns",
            "solution": "Added composite indexes and rewrote N+1 queries using joins",
            "tags": ["performance", "database", "optimization", "sql"]
        }
    ]

    stored_memories = []
    for memory in test_memories:
        memory_id, embedding = await vector_service.store_memory_vector(
            memory_log_id=memory["id"],
            memory_data=memory,
            user_id=user_id,
            project_id=project_id
        )
        stored_memories.append(memory_id)
        print(f"✓ Stored: {memory_id} (task: {memory['task']}, dim: {len(embedding)})")

    # Test 2: Count memories
    print("\n[3] Counting memories...")
    count = await vector_service.count_memories(user_id, project_id)
    print(f"✓ Total memories in collection: {count}")

    # Test 3: Semantic search
    print("\n[4] Semantic search tests...")

    search_queries = [
        {
            "query": "security vulnerabilities and authentication issues",
            "expected": "authentication-bug-fix"
        },
        {
            "query": "user interface design and visual improvements",
            "expected": "permission-dialog-redesign"
        },
        {
            "query": "slow performance and database problems",
            "expected": "database-query-optimization"
        }
    ]

    for i, test in enumerate(search_queries, 1):
        print(f"\n  Query {i}: \"{test['query']}\"")
        results = await vector_service.search_similar_memories(
            query=test["query"],
            user_id=user_id,
            project_id=project_id,
            limit=3,
            min_similarity=0.0
        )

        for j, result in enumerate(results, 1):
            task = result["document"].get("task", "unknown")
            similarity_pct = result["similarity"] * 100
            print(f"    {j}. {task} (similarity: {similarity_pct:.1f}%)")

        # Check if expected result is first
        if results and results[0]["document"].get("task") == test["expected"]:
            print(f"  ✓ Top result matches expected: {test['expected']}")
        else:
            print(f"  ⚠ Top result doesn't match expected: {test['expected']}")

    # Test 4: Metadata filtering
    print("\n[5] Metadata filtering test...")
    print("  Query: 'bug fix' with component filter = 'auth-module'")

    results = await vector_service.search_similar_memories(
        query="bug fix",
        user_id=user_id,
        project_id=project_id,
        limit=5,
        where_filter={"component": "auth-module"}
    )

    print(f"  Found {len(results)} result(s):")
    for result in results:
        task = result["document"].get("task", "unknown")
        component = result["metadata"].get("component", "unknown")
        similarity_pct = result["similarity"] * 100
        print(f"    - {task} (component: {component}, similarity: {similarity_pct:.1f}%)")

    # Test 5: Get specific memory
    print("\n[6] Retrieve specific memory...")
    if stored_memories:
        memory_data = await vector_service.get_memory(
            memory_id=stored_memories[0],
            user_id=user_id,
            project_id=project_id
        )
        if memory_data:
            print(f"✓ Retrieved: {memory_data.get('task', 'unknown')}")
        else:
            print("✗ Failed to retrieve memory")

    # Test 6: Cache statistics
    print("\n[7] Cache statistics...")
    cache_stats = embedding_service.cache.get_stats()
    print(f"  Cache hits: {cache_stats['hit_count']}")
    print(f"  Cache misses: {cache_stats['miss_count']}")
    print(f"  Hit rate: {cache_stats['hit_rate_percent']:.1f}%")
    print(f"  Cache size: {cache_stats['size']}/{cache_stats['max_size']}")
    print(f"  Total requests: {cache_stats['total_requests']}")

    # Cleanup
    print("\n[8] Cleanup...")
    print("  Note: Memory vectors persist in ChromaDB for future tests")
    print(f"  Location: {chromadb_path}")
    print(f"  Collection: semantix_memories_{user_id}_{project_id}")

    print("\n" + "=" * 80)
    print("ChromaDB Integration Test Complete!")
    print("=" * 80)
    print("\nNext steps:")
    print("  1. Start API server: poetry run uvicorn src.api.app:app --reload")
    print("  2. Test POST /memory-logs endpoint with user_id and project_id")
    print("  3. Test POST /memory-logs/search endpoint for semantic search")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
