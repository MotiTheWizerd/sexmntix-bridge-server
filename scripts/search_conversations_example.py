"""
Example script: Search conversations using pgvector semantic similarity.

This demonstrates how to:
1. Generate an embedding for a search query
2. Use ConversationRepository.search_similar() to find relevant conversations
3. Display results with similarity scores

Usage:
    poetry run python scripts/search_conversations_example.py "what did we discuss about pgvector?"
    poetry run python scripts/search_conversations_example.py "conversation embeddings population"
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

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
from src.modules.core import EventBus, Logger
from src.modules.embeddings import (
    EmbeddingService,
    GoogleEmbeddingProvider,
    ProviderConfig,
    EmbeddingCache,
)


async def search_conversations(query: str, user_id: str = None, limit: int = 5, save_to_file: bool = False):
    """
    Search conversations using semantic similarity.

    Args:
        query: Natural language search query
        user_id: Optional user_id filter
        limit: Maximum number of results
        save_to_file: Save full results to JSON file
    """
    print("\n🔍 Conversation Semantic Search")
    print("=" * 70)
    print(f"Query: {query}")
    print(f"User filter: {user_id or 'None (all users)'}")
    print(f"Limit: {limit}")
    print()

    # Load configuration
    load_dotenv()
    app_config = load_app_config()
    service_config = load_service_config()

    # Initialize database
    db_manager = DatabaseManager(app_config.database_url)

    # Initialize embedding service
    event_bus = EventBus()
    logger = Logger("search-conversations")

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

    try:
        # Generate embedding for the query
        print("⏳ Generating query embedding...")
        query_embedding_result = await embedding_service.generate_embedding(query)
        query_embedding = query_embedding_result.embedding
        print(f"✓ Generated embedding ({len(query_embedding)} dimensions)")
        print()

        # Search conversations
        async with db_manager.session_factory() as session:
            repo = ConversationRepository(session)

            results = await repo.search_similar(
                query_embedding=query_embedding,
                user_id=user_id,
                limit=limit,
                min_similarity=0.3,  # 30% minimum similarity
                distance_metric="cosine"
            )

        # Display results
        if not results:
            print("❌ No conversations found matching your query")
            print()
            return

        print(f"📊 Found {len(results)} matching conversation(s):")
        print()

        # Prepare results for display and file
        formatted_results = []

        for i, (conversation, similarity) in enumerate(results, 1):
            # Parse conversation messages
            messages = conversation.raw_data.get('conversation', [])

            # Get first user message for preview
            user_msg = next((m for m in messages if m.get('role') == 'user'), None)
            user_preview = (user_msg.get('text', '')[:100] + '...'
                          if user_msg and len(user_msg.get('text', '')) > 100
                          else user_msg.get('text', '') if user_msg else '[No user message]')

            # Get assistant response count
            assistant_msgs = [m for m in messages if m.get('role') == 'assistant']

            # Display summary
            print(f"{i}. Similarity: {similarity:.1%} | ID: {conversation.id[:8]}...")
            print(f"   Model: {conversation.model}")
            print(f"   User: {conversation.user_id}")
            print(f"   Session: {conversation.session_id or 'None'}")
            print(f"   Created: {conversation.created_at}")
            print(f"   Messages: {len(messages)} ({len(assistant_msgs)} assistant responses)")
            print(f"   Preview: {user_preview}")
            print()

            # Store full result
            formatted_results.append({
                "rank": i,
                "similarity": float(similarity),
                "id": conversation.id,
                "conversation_id": conversation.conversation_id,
                "model": conversation.model,
                "user_id": conversation.user_id,
                "project_id": conversation.project_id,
                "session_id": conversation.session_id,
                "created_at": conversation.created_at.isoformat(),
                "messages": messages,
                "raw_data": conversation.raw_data
            })

        # Save to file if requested
        if save_to_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"conversation_search_results_{timestamp}.json"
            output_path = Path(__file__).parent / filename

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "query": query,
                    "user_filter": user_id,
                    "limit": limit,
                    "result_count": len(formatted_results),
                    "timestamp": datetime.now().isoformat(),
                    "results": formatted_results
                }, f, indent=2, ensure_ascii=False)

            print(f"💾 Full results saved to: {output_path}")
            print()

    finally:
        await embedding_service.close()
        await db_manager.close()


async def summarize_today_conversations(user_id: str = None):
    """
    Get all conversations from today and provide a summary.

    Args:
        user_id: Optional user_id filter
    """
    print("\n📅 Today's Conversations Summary")
    print("=" * 70)
    print(f"User filter: {user_id or 'None (all users)'}")
    print()

    # Load configuration
    load_dotenv()
    app_config = load_app_config()
    db_manager = DatabaseManager(app_config.database_url)

    try:
        # Calculate today's date range
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)

        async with db_manager.session_factory() as session:
            repo = ConversationRepository(session)

            # Get today's conversations
            from sqlalchemy import select, and_
            from src.database.models import Conversation

            conditions = [
                Conversation.created_at >= today,
                Conversation.created_at < tomorrow
            ]

            if user_id:
                conditions.append(Conversation.user_id == user_id)

            result = await session.execute(
                select(Conversation)
                .where(and_(*conditions))
                .order_by(Conversation.created_at)
            )
            conversations = list(result.scalars().all())

        if not conversations:
            print("❌ No conversations found for today")
            print()
            return

        print(f"📊 Found {len(conversations)} conversation(s) today")
        print()

        # Group by user
        by_user = {}
        for conv in conversations:
            if conv.user_id not in by_user:
                by_user[conv.user_id] = []
            by_user[conv.user_id].append(conv)

        # Display summary
        for uid, convs in by_user.items():
            print(f"User: {uid}")
            print(f"  Conversations: {len(convs)}")

            # Count total messages
            total_msgs = sum(len(c.raw_data.get('conversation', [])) for c in convs)
            print(f"  Total messages: {total_msgs}")

            # Show sessions
            sessions = set(c.session_id for c in convs if c.session_id)
            if sessions:
                print(f"  Sessions: {len(sessions)}")

            # Show models used
            models = set(c.model for c in convs)
            print(f"  Models: {', '.join(models)}")

            print()

        # Show timeline
        print("Timeline:")
        for conv in conversations[:10]:  # Show first 10
            messages = conv.raw_data.get('conversation', [])
            user_msg = next((m for m in messages if m.get('role') == 'user'), None)
            preview = (user_msg.get('text', '')[:60] + '...'
                      if user_msg and len(user_msg.get('text', '')) > 60
                      else user_msg.get('text', '') if user_msg else '[No message]')

            time_str = conv.created_at.strftime('%H:%M:%S')
            print(f"  {time_str} | {conv.id[:8]}... | {preview}")

        if len(conversations) > 10:
            print(f"  ... and {len(conversations) - 10} more")
        print()

    finally:
        await db_manager.close()


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("\n📚 Conversation Search Examples")
        print("=" * 70)
        print()
        print("Usage:")
        print('  poetry run python scripts/search_conversations_example.py "your search query"')
        print('  poetry run python scripts/search_conversations_example.py --today')
        print()
        print("Examples:")
        print('  poetry run python scripts/search_conversations_example.py "pgvector implementation"')
        print('  poetry run python scripts/search_conversations_example.py "conversation embeddings" --save')
        print('  poetry run python scripts/search_conversations_example.py --today')
        print('  poetry run python scripts/search_conversations_example.py --today --user-id "84e17260-ff03-409b-bf30-0b5ba52a2ab4"')
        print()
        print("Flags:")
        print("  --save          Save full conversation details to JSON file")
        print("  --user-id ID    Filter by specific user ID")
        print()
        sys.exit(0)

    # Parse arguments
    if sys.argv[1] == "--today":
        user_id = None
        if len(sys.argv) > 3 and sys.argv[2] == "--user-id":
            user_id = sys.argv[3]
        asyncio.run(summarize_today_conversations(user_id))
    else:
        query = sys.argv[1]
        user_id = None
        save_to_file = False

        # Check for optional flags
        for i in range(2, len(sys.argv)):
            if sys.argv[i] == "--save":
                save_to_file = True
            elif sys.argv[i] == "--user-id" and i + 1 < len(sys.argv):
                user_id = sys.argv[i + 1]

        asyncio.run(search_conversations(query, user_id, save_to_file=save_to_file))


if __name__ == "__main__":
    main()
