"""
Test harness for conversation-based required memory retrieval.

Usage:
  python scripts/test_required_memory.py

Environment:
  - Requires Postgres connection via DATABASE_URL (loaded by app init).
  - Requires embedding service env (e.g., OPENAI_API_KEY/OPENAI_BASE_URL/OPENAI_MODEL).
"""

import argparse
import asyncio
import json
from typing import List

from src.database import DatabaseManager
from src.modules.core import EventBus
from src.modules.core.telemetry.logger import get_logger
from src.services.conversation_memory_retrieval_service import (
    ConversationMemoryRetrievalService,
)
from src.modules.SXPrefrontal import ICMBrain
from src.api.bootstrap.config import load_app_config, load_service_config
from src.api.bootstrap.services.embedding_service import initialize_embedding_service
from datetime import datetime


async def main():
    parser = argparse.ArgumentParser(description="Test ICM -> conversation memory retrieval")
    parser.add_argument(
        "--query",
        type=str,
        default=None,
        help="Run a single query instead of the sample set",
    )
    args = parser.parse_args()

    app_config = load_app_config()
    service_config = load_service_config()
    db_manager = DatabaseManager(app_config.database_url)

    # Lightweight wiring for embedding service
    logger = get_logger("test_required_memory")
    event_bus = EventBus()
    embedding_service = initialize_embedding_service(
        config=service_config,
        event_bus=event_bus,
        logger=logger,
    )
    if embedding_service is None:
        raise RuntimeError("Embedding service not available. Set GOOGLE_API_KEY/EMBEDDING_MODEL envs.")
    retrieval_service = ConversationMemoryRetrievalService(
        db_manager=db_manager,
        embedding_service=embedding_service,
        default_limit=5,
        default_min_similarity=0.5,
    )

    icm = ICMBrain()

    samples: List[str] = (
        [args.query]
        if args.query
        else [
            "Can you summarize our authentication plans from last week?",
            "What did we decide about rate limiting yesterday?",
            "hi",
            "Book a meeting with the infra team tomorrow",
        ]
    )

    for text in samples:
        icm_result = icm.classify(text)
        print("=" * 70)
        print("User:", text)
        print("ICM:", json.dumps(icm_result, indent=2))

        retrieval_strategy = icm_result.get("retrieval_strategy", "none")
        required_memory = icm_result.get("required_memory", [])

        if retrieval_strategy == "none" or not required_memory:
            print("Retrieval skipped (strategy none or no required_memory).")
            continue

        results = await retrieval_service.fetch_required_memory(
            required_memory=required_memory,
            retrieval_strategy=retrieval_strategy,
            user_id=None,
            project_id=None,
            limit=5,
            min_similarity=0.5,
            time_text=text,
            now=datetime.utcnow(),
        )

        print("Results:")
        print(json.dumps(results, indent=2))

    await db_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
