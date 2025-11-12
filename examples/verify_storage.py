"""
Verify ChromaDB and PostgreSQL Storage

Checks if data is persisted in both databases.
"""

import os
import sys
import chromadb
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def verify_chromadb():
    """Verify ChromaDB storage."""
    print("=" * 80)
    print("ChromaDB Storage Verification")
    print("=" * 80)

    chromadb_path = os.getenv("CHROMADB_PATH", "./data/chromadb")
    print(f"\nChromaDB Path: {chromadb_path}")

    # Check if directory exists
    if not os.path.exists(chromadb_path):
        print("❌ ChromaDB directory does NOT exist")
        return

    print("✓ ChromaDB directory exists")

    # List directory contents
    print(f"\nDirectory contents:")
    for item in os.listdir(chromadb_path):
        item_path = os.path.join(chromadb_path, item)
        if os.path.isfile(item_path):
            size = os.path.getsize(item_path)
            print(f"  - {item} ({size:,} bytes)")
        else:
            print(f"  - {item}/ (directory)")

    # Connect to ChromaDB
    try:
        client = chromadb.PersistentClient(path=chromadb_path)
        print("\n✓ Successfully connected to ChromaDB")
    except Exception as e:
        print(f"\n❌ Failed to connect to ChromaDB: {e}")
        return

    # List all collections
    collections = client.list_collections()
    print(f"\nTotal collections: {len(collections)}")

    if not collections:
        print("⚠ No collections found")
        return

    print("\nCollections:")
    for collection in collections:
        print(f"\n  Collection: {collection.name}")
        print(f"    Count: {collection.count()}")
        print(f"    Metadata: {collection.metadata}")

        # Get first few items
        try:
            results = collection.get(limit=3, include=["documents", "metadatas"])

            if results['ids']:
                print(f"    Sample items:")
                import json
                for i, (doc_id, doc, meta) in enumerate(zip(
                    results['ids'],
                    results['documents'],
                    results['metadatas']
                ), 1):
                    doc_data = json.loads(doc)
                    print(f"      {i}. ID: {doc_id}")
                    print(f"         Task: {doc_data.get('task', 'unknown')}")
                    print(f"         Component: {meta.get('component', 'N/A')}")
        except Exception as e:
            print(f"    Error reading items: {e}")


def verify_postgresql():
    """Verify PostgreSQL storage."""
    print("\n" + "=" * 80)
    print("PostgreSQL Storage Verification")
    print("=" * 80)

    try:
        import asyncio
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text

        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            print("❌ DATABASE_URL not found in .env")
            return

        print(f"\nDatabase URL: {database_url.split('@')[1] if '@' in database_url else 'configured'}")

        async def check_db():
            # Create engine
            engine = create_async_engine(database_url, echo=False)

            try:
                async with engine.begin() as conn:
                    # Check if memory_logs table exists
                    result = await conn.execute(text("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables
                            WHERE table_name = 'memory_logs'
                        );
                    """))
                    table_exists = result.scalar()

                    if not table_exists:
                        print("\n❌ memory_logs table does NOT exist")
                        print("   Run migration: poetry run alembic upgrade head")
                        return

                    print("\n✓ memory_logs table exists")

                    # Check table structure
                    result = await conn.execute(text("""
                        SELECT column_name, data_type, is_nullable
                        FROM information_schema.columns
                        WHERE table_name = 'memory_logs'
                        ORDER BY ordinal_position;
                    """))

                    print("\nTable structure:")
                    columns = result.fetchall()
                    for col in columns:
                        nullable = "NULL" if col[2] == "YES" else "NOT NULL"
                        print(f"  - {col[0]}: {col[1]} ({nullable})")

                    # Check if embedding field exists
                    has_embedding = any(col[0] == 'embedding' for col in columns)
                    has_user_id = any(col[0] == 'user_id' for col in columns)
                    has_project_id = any(col[0] == 'project_id' for col in columns)

                    if has_embedding:
                        print("\n✓ 'embedding' field exists")
                    else:
                        print("\n❌ 'embedding' field NOT found")
                        print("   Run migration: poetry run alembic upgrade head")

                    if has_user_id and has_project_id:
                        print("✓ 'user_id' and 'project_id' fields exist")
                    else:
                        print("❌ 'user_id' or 'project_id' fields NOT found")
                        print("   Run migration: poetry run alembic upgrade head")

                    # Count records
                    result = await conn.execute(text("""
                        SELECT COUNT(*) FROM memory_logs;
                    """))
                    total_count = result.scalar()
                    print(f"\nTotal memory_logs: {total_count}")

                    if total_count > 0:
                        # Count records with embeddings
                        result = await conn.execute(text("""
                            SELECT COUNT(*) FROM memory_logs
                            WHERE embedding IS NOT NULL;
                        """))
                        with_embeddings = result.scalar()

                        print(f"  With embeddings: {with_embeddings}")
                        print(f"  Without embeddings: {total_count - with_embeddings}")

                        # Show sample records
                        result = await conn.execute(text("""
                            SELECT
                                id,
                                task,
                                user_id,
                                project_id,
                                CASE
                                    WHEN embedding IS NULL THEN 'No'
                                    ELSE 'Yes (' || array_length(embedding, 1) || 'D)'
                                END as has_embedding,
                                created_at
                            FROM memory_logs
                            ORDER BY id DESC
                            LIMIT 5;
                        """))

                        records = result.fetchall()
                        if records:
                            print("\nRecent records:")
                            for rec in records:
                                print(f"  ID {rec[0]}: {rec[1]}")
                                print(f"    User: {rec[2] or 'N/A'}, Project: {rec[3] or 'N/A'}")
                                print(f"    Embedding: {rec[4]}")
                                print(f"    Created: {rec[5]}")

            except Exception as e:
                print(f"\n❌ Database error: {e}")
            finally:
                await engine.dispose()

        # Run async check
        asyncio.run(check_db())

    except ImportError as e:
        print(f"❌ Failed to import database libraries: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Run all verifications."""
    verify_chromadb()
    verify_postgresql()

    print("\n" + "=" * 80)
    print("Verification Complete!")
    print("=" * 80)
    print("\nSummary:")
    print("  1. ChromaDB stores vectors for semantic search (HNSW index)")
    print("  2. PostgreSQL stores full records with embeddings")
    print("  3. Both storages work together for complete functionality")
    print("=" * 80)


if __name__ == "__main__":
    main()
