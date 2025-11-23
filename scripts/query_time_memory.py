"""
Time-Based Conversational Memory Query Script.

This script answers natural language questions about conversations within specific
time ranges using hybrid search: pgvector semantic similarity + date filtering.

Features:
- Time expressions: "2-hours-ago", "last-hour", "yesterday", "today"
- Semantic search within time windows
- Optional LLM synthesis for natural summaries
- Multi-tenant user/project filtering

Usage:
    # Basic time query
    poetry run python scripts/query_time_memory.py "What did we discuss?" --time "2-hours-ago"

    # With user filter
    poetry run python scripts/query_time_memory.py "Summarize" --time "yesterday" --user-id "user-123"

    # With LLM synthesis
    poetry run python scripts/query_time_memory.py "What happened?" --time "today" --synthesize

    # Save to JSON
    poetry run python scripts/query_time_memory.py "Recent work" --time "last-hour" --save

Examples:
    poetry run python scripts/query_time_memory.py "pgvector implementation" --time "yesterday"
    poetry run python scripts/query_time_memory.py "bugs and fixes" --time "2-hours-ago" --synthesize
    poetry run python scripts/query_time_memory.py "what did we build" --time "today" --user-id "84e17260-ff03-409b-bf30-0b5ba52a2ab4"
"""
output_data =""
import asyncio
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Optional

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Setup paths
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
from src.api.bootstrap.config import load_app_config, load_service_config
from src.database import DatabaseManager
from src.database.repositories.conversation_repository import ConversationRepository
from src.database.models import Conversation
from src.modules.core import EventBus, Logger
from src.modules.embeddings import (
    EmbeddingService,
    GoogleEmbeddingProvider,
    ProviderConfig,
    EmbeddingCache,
)
from src.modules.llm.service import LLMService
from src.modules.SXThalamus.prompts import SXThalamusPromptBuilder
from src.utils.date_range_calculator import DateRangeCalculator


def format_time_range(start: datetime, end: datetime) -> str:
    """Format time range for display."""
    if start.date() == end.date():
        # Same day - show time range
        return f"{start.strftime('%Y-%m-%d %H:%M')} to {end.strftime('%H:%M')}"
    else:
        # Different days - show full range
        return f"{start.strftime('%Y-%m-%d %H:%M')} to {end.strftime('%Y-%m-%d %H:%M')}"


def display_conversation_preview(conv: Conversation, rank: int, similarity: float):
    """Display a conversation result with preview."""
    print(f"\n{'─' * 70}")
    print(f"Rank #{rank} | Similarity: {similarity:.4f} ({similarity * 100:.1f}%)")
    print(f"{'─' * 70}")

    # Metadata
    print(f"📅 Created: {conv.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"🆔 ID: {conv.conversation_id}")
    print(f"🤖 Model: {conv.model}")

    if conv.session_id:
        print(f"📎 Session: {conv.session_id}")

    # Extract messages from raw_data
    messages = conv.raw_data.get('conversation', [])

    print(f"\n💬 Conversation ({len(messages)} messages):")
    print()

    # Show first few message exchanges
    for i, msg in enumerate(messages[:6]):  # Show up to 6 messages (3 exchanges)
        role = msg.get('role', 'unknown')
        text = msg.get('text', '')

        # Truncate long messages
        if len(text) > 200:
            text = text[:200] + "..."

        role_emoji = "👤" if role == "user" else "🤖"
        print(f"  {role_emoji} {role.upper()}: {text}")

    if len(messages) > 6:
        print(f"  ... ({len(messages) - 6} more messages)")


def format_synthesize_ready(
    query: str,
    time_expression: str,
    start_time: datetime,
    end_time: datetime,
    results: List[Tuple[Conversation, float]]
):
    """
    Format results in clean, LLM-ready format - just the dialogue.

    Args:
        query: The search query
        time_expression: Time period expression
        start_time: Start of time range
        end_time: End of time range
        results: List of (Conversation, similarity) tuples
    """
    output = []

    # Each conversation - just the messages
    for i, (conv, similarity) in enumerate(results, 1):
        # Extract messages
        messages = conv.raw_data.get('conversation', [])

        for msg in messages:
            role = msg.get('role', 'unknown')
            text = msg.get('text', '').strip()

            if role == 'user':
                output.append(f"User: {text}")
            elif role == 'assistant':
                output.append(f"Assistant: {text}")
            else:
                output.append(f"{role.title()}: {text}")

            output.append("")  # Blank line between messages

        # Add separator between conversations if there are multiple
        if i < len(results):
            output.append("─" * 80)
            output.append("")

    return "\n".join(output)


async def query_time_memory(
    query: str,
    time_expression: str,
    user_id: Optional[str] = None,
    project_id: Optional[str] = None,
    limit: int = 5,
    min_similarity: float = 0.3,
    synthesize: bool = False,
    synthesize_ready: bool = False,
    save_to_file: bool = False
):
    """
    Query conversational memory within a time range.

    Args:
        query: Natural language search query
        time_expression: Time period (e.g., "2-hours-ago", "yesterday", "today")
        user_id: Optional user_id filter
        project_id: Optional project_id filter
        limit: Maximum number of results
        min_similarity: Minimum similarity threshold (0.0 to 1.0)
        synthesize: Use LLM to synthesize natural language summary
        synthesize_ready: Output clean format ready for LLM prompts (no emojis/noise)
        save_to_file: Save results to JSON file
    """
    print("\n🧠 Time-Based Conversational Memory Query")
    print("=" * 70)
    print(f"Query: {query}")
    print(f"Time period: {time_expression}")
    print(f"User filter: {user_id or 'None (all users)'}")
    print(f"Project filter: {project_id or 'None (all projects)'}")
    print(f"Min similarity: {min_similarity}")
    print(f"Limit: {limit}")
    print(f"Synthesize: {'Yes' if synthesize else 'No'}")
    print()

    # Load configuration
    load_dotenv()
    app_config = load_app_config()
    service_config = load_service_config()

    # Initialize services
    db_manager = DatabaseManager(app_config.database_url)
    event_bus = EventBus()
    logger = Logger("query-time-memory")

    # Embedding service
    embedding_config = ProviderConfig(
        provider_name=service_config.embedding.provider_name,
        model_name=service_config.embedding.model_name,
        api_key=service_config.embedding.api_key,
        timeout_seconds=service_config.embedding.timeout_seconds,
        max_retries=service_config.embedding.max_retries
    )

    provider = GoogleEmbeddingProvider(embedding_config)
    embedding_service = EmbeddingService(
        event_bus=event_bus,
        logger=logger,
        provider=provider,
        cache=EmbeddingCache(),
        cache_enabled=True
    )

    # LLM service (only if synthesis requested)
    llm_service = None
    if synthesize:
        llm_service = LLMService(db_manager=db_manager)

    try:
        # Parse time expression
        print("⏳ Parsing time range...")
        start_time, end_time = DateRangeCalculator.calculate(time_period=time_expression)

        if start_time is None or end_time is None:
            print(f"❌ Error: Invalid time expression '{time_expression}'")
            print("\nSupported formats:")
            print("  - last-hour")
            print("  - 2-hours-ago, 3-hours-ago, etc.")
            print("  - yesterday")
            print("  - today")
            print("  - recent / last-week (7 days)")
            print("  - last-month (30 days)")
            return

        print(f"✓ Time range: {format_time_range(start_time, end_time)}")
        print()

        # Generate query embedding
        print("⏳ Generating query embedding...")
        query_embedding_result = await embedding_service.generate_embedding(query)
        query_embedding = query_embedding_result.embedding
        print(f"✓ Generated embedding ({len(query_embedding)} dimensions)")
        print()

        # Hybrid search: time + semantic
        print("🔍 Searching conversations (time range + semantic similarity)...")
        async with db_manager.session_factory() as session:
            repo = ConversationRepository(session)

            results = await repo.search_similar_by_time_range(
                query_embedding=query_embedding,
                start_time=start_time,
                end_time=end_time,
                user_id=user_id,
                project_id=project_id,
                limit=limit,
                min_similarity=min_similarity,
                distance_metric="cosine"
            )

        # Display results
        print(f"✓ Found {len(results)} relevant conversations")

        if len(results) == 0:
            print("\n❌ No conversations found matching your criteria.")
            print("\nTry:")
            print("  - Lowering --min-similarity (current: {:.2f})".format(min_similarity))
            print("  - Using a broader time period")
            print("  - Checking if conversations exist in this time range")
            return

        # Show results based on format
        if synthesize_ready:
            # Clean format ready for LLM prompts - just the dialogue
            clean_output = format_synthesize_ready(
                query=query,
                time_expression=time_expression,
                start_time=start_time,
                end_time=end_time,
                results=results
            )
            print()
            print(clean_output)
        else:
            # Show individual results with emojis and formatting
            print("\n" + "=" * 70)
            print("SEARCH RESULTS")
            print("=" * 70)

            for i, (conv, similarity) in enumerate(results, 1):
                display_conversation_preview(conv, i, similarity)

        # Optional: LLM Synthesis
        if synthesize and llm_service:
            print("\n" + "=" * 70)
            print("🤖 LLM MEMORY SYNTHESIS")
            print("=" * 70)
            print("⏳ Generating natural language summary...\n")

            # Format results for synthesis
            formatted_results = []
            for i, (conv, similarity) in enumerate(results, 1):
                messages = conv.raw_data.get('conversation', [])
                formatted_results.append({
                    "similarity": similarity,
                    "created_at": conv.created_at.isoformat(),
                    "messages": messages
                })

            # Build synthesis prompt
            prompt_builder = SXThalamusPromptBuilder()
            prompt = prompt_builder.build_memory_synthesis_prompt(
                formatted_results,
                query=f"{query} (from {time_expression})"
            )

            # Generate synthesis
            synthesis = await llm_service.generate_content(
                prompt=prompt,
                user_id=user_id or "default",
                worker_type="memory_synthesizer"
            )

            print(synthesis)
            output_data=synthesis
            print()

        # Optional: Save to JSON
        if save_to_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"time_memory_results_{timestamp}.json"
            filepath = Path(__file__).parent / filename

            if synthesize_ready:
                # Clean, synthesis-ready JSON format
                # output_data = {
                #     "query": query,
                #     "time_range": {
                #         "start": start_time.isoformat(),
                #         "end": end_time.isoformat(),
                #         "expression": time_expression
                #     },
                #     "result_count": len(results),
                #     "conversations": [
                #         {
                #             "rank": i,
                #             "similarity": round(similarity, 4),
                #             "created_at": conv.created_at.isoformat(),
                #             "dialogue": [
                #                 {
                #                     "role": msg.get('role', 'unknown'),
                #                     "content": msg.get('text', '').strip()
                #                 }
                #                 for msg in conv.raw_data.get('conversation', [])
                #             ]
                #         }
                #         for i, (conv, similarity) in enumerate(results, 1)
                #     ]
                # }
             print('skip')
            else:
                # Full detailed JSON format
                output_data = {
                    "query": query,
                    "time_expression": time_expression,
                    "time_range": {
                        "start": start_time.isoformat(),
                        "end": end_time.isoformat()
                    },
                    "user_filter": user_id,
                    "project_filter": project_id,
                    "limit": limit,
                    "min_similarity": min_similarity,
                    "result_count": len(results),
                    "timestamp": datetime.now().isoformat(),
                    "results": [
                        {
                            "rank": i,
                            "similarity": similarity,
                            "id": conv.id,
                            "conversation_id": conv.conversation_id,
                            "model": conv.model,
                            "user_id": conv.user_id,
                            "project_id": conv.project_id,
                            "session_id": conv.session_id,
                            "created_at": conv.created_at.isoformat(),
                            "messages": conv.raw_data.get('conversation', []),
                            "raw_data": conv.raw_data
                        }
                        for i, (conv, similarity) in enumerate(results, 1)
                    ]
                }

            if synthesize_ready:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(output_data, f, indent=2, ensure_ascii=False)
            else:
                with open(filepath, 'w', encoding='utf-8') as f:
                    output_data    
            print(f"\n💾 Results saved to: {filename}")

        print("\n✅ Query completed successfully!")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Query conversational memory within time ranges using hybrid search.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "What did we discuss?" --time "2-hours-ago"
  %(prog)s "Summarize conversations" --time "yesterday" --synthesize
  %(prog)s "Recent work" --time "today" --user-id "user-123"
  %(prog)s "pgvector bugs" --time "last-hour" --save

Supported time expressions:
  last-hour           Last 1 hour
  2-hours-ago         Last 2 hours (any N)
  yesterday           Previous full day (00:00-23:59)
  today               Current day so far
  recent/last-week    Last 7 days
  last-month          Last 30 days
        """
    )

    parser.add_argument(
        "query",
        type=str,
        help="Natural language search query"
    )

    parser.add_argument(
        "--time",
        type=str,
        required=True,
        help="Time period expression (e.g., '2-hours-ago', 'yesterday', 'today')"
    )

    parser.add_argument(
        "--user-id",
        type=str,
        default=None,
        help="Filter by user ID (optional)"
    )

    parser.add_argument(
        "--project-id",
        type=str,
        default=None,
        help="Filter by project ID (optional)"
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Maximum number of results (default: 5)"
    )

    parser.add_argument(
        "--min-similarity",
        type=float,
        default=0.3,
        help="Minimum similarity threshold 0.0-1.0 (default: 0.3)"
    )

    parser.add_argument(
        "--synthesize",
        action="store_true",
        help="Use LLM to generate natural language summary"
    )

    parser.add_argument(
        "--synthesize-ready",
        action="store_true",
        help="Output clean format ready for LLM prompts (no emojis/noise)"
    )

    parser.add_argument(
        "--save",
        action="store_true",
        help="Save results to JSON file"
    )

    args = parser.parse_args()

    # Run async query
    asyncio.run(query_time_memory(
        query=args.query,
        time_expression=args.time,
        user_id=args.user_id,
        project_id=args.project_id,
        limit=args.limit,
        min_similarity=args.min_similarity,
        synthesize=args.synthesize,
        synthesize_ready=args.synthesize_ready,
        save_to_file=args.save
    ))


if __name__ == "__main__":
    main()
