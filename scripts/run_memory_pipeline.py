"""
Pipeline runner: Intent ICM -> Time ICM -> conversation retrieval.

Usage:
  python scripts/run_memory_pipeline.py --query "what did we talk about last night?"
  python scripts/run_memory_pipeline.py --limit 5
"""

import argparse
import asyncio
import json
from datetime import datetime, timezone

from src.api.bootstrap.config import load_app_config, load_service_config
from src.api.bootstrap.services.embedding_service import initialize_embedding_service
from src.database import DatabaseManager
from src.modules.core import EventBus
from src.modules.core.telemetry.logger import get_logger
from src.modules.SXPrefrontal import ICMBrain, TimeICMBrain
from src.services.conversation_memory_retrieval_service import (
    ConversationMemoryRetrievalService,
)


def parse_args():
    parser = argparse.ArgumentParser(description="ICM + TimeICM + Retrieval pipeline")
    parser.add_argument("--query", type=str, required=True, help="User query")
    parser.add_argument("--limit", type=int, default=5, help="Result limit")
    parser.add_argument("--min-similarity", type=float, default=0.5, help="Min similarity")
    parser.add_argument("--tz-offset", type=int, default=None, help="Timezone offset minutes (e.g., 120 for UTC+2)")
    return parser.parse_args()


async def main():
    args = parse_args()
    user_text = args.query
    now = datetime.now(timezone.utc)

    # Configs
    app_config = load_app_config()
    service_config = load_service_config()

    # Services
    db_manager = DatabaseManager(app_config.database_url)
    logger = get_logger("pipeline")
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
        default_limit=args.limit,
        default_min_similarity=args.min_similarity,
    )

    intent_icm = ICMBrain()
    time_icm = TimeICMBrain()

    # Step 1: Intent ICM
    intent_result = intent_icm.classify(user_text)
    print("=" * 70)
    print("Intent ICM:")
    print(json.dumps(intent_result, indent=2))

    # Step 2: Time ICM (always run; may return null start/end)
    time_result = time_icm.resolve(
        user_text,
        now=now,
        tz_offset_minutes=args.tz_offset,
    )
    print("=" * 70)
    print("Time ICM:")
    print(json.dumps(time_result, indent=2))

    # Normalize time window
    start_time = time_result.get("start_time")
    end_time = time_result.get("end_time")
    start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00")) if isinstance(start_time, str) else None
    end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00")) if isinstance(end_time, str) else None

    # Retrieval parameters
    retrieval_strategy = intent_result.get("retrieval_strategy", "none")
    required_memory = intent_result.get("required_memory", [])

    if retrieval_strategy == "none" or not required_memory:
        print("Retrieval skipped (strategy none or no required_memory).")
        await db_manager.close()
        return

    print("=" * 70)
    print("Retrieval Request:")
    print(json.dumps({
        "retrieval_strategy": retrieval_strategy,
        "required_memory": required_memory,
        "start_time": start_time,
        "end_time": end_time,
        "min_similarity": args.min_similarity,
        "limit": args.limit,
    }, indent=2))

    results = await retrieval_service.fetch_required_memory(
        required_memory=required_memory,
        retrieval_strategy=retrieval_strategy,
        user_id=None,
        project_id=None,
        limit=args.limit,
        min_similarity=args.min_similarity,
        start_time=start_dt,
        end_time=end_dt,
        time_text=user_text,
        tz_offset_minutes=args.tz_offset,
        now=now,
    )

    print("=" * 70)
    print("Results:")
    print(json.dumps(results, indent=2))

    await db_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
