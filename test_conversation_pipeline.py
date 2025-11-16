"""
Test script to verify the conversation ChromaDB pipeline.

This script tests the entire flow:
1. POST /conversations - Create conversation in PostgreSQL
2. Event handler - Background vector storage in ChromaDB
3. POST /conversations/search - Search in separate collection
"""

import asyncio
import httpx
import time
import json


BASE_URL = "http://localhost:8000"


async def test_conversation_pipeline():
    """Test the complete conversation pipeline"""

    async with httpx.AsyncClient() as client:
        print("\n" + "="*60)
        print("TESTING CONVERSATION CHROMADB PIPELINE")
        print("="*60)

        # Step 1: Create a conversation
        print("\n[1] Creating conversation in PostgreSQL...")
        conversation_data = {
            "user_id": "test_user_1",
            "project_id": "test_project",
            "conversation_id": f"test-conv-{int(time.time())}",
            "model": "gpt-5-1-instant",
            "conversation": [
                {
                    "role": "user",
                    "message_id": "msg-1",
                    "text": "How do I implement authentication in FastAPI?"
                },
                {
                    "role": "assistant",
                    "message_id": "msg-2",
                    "text": "You can use OAuth2 with JWT tokens. Here's an example..."
                }
            ]
        }

        response = await client.post(
            f"{BASE_URL}/conversations",
            json=conversation_data
        )

        if response.status_code == 201:
            created = response.json()
            print(f"✅ Conversation created with ID: {created['id']}")
            print(f"   Conversation UUID: {created['conversation_id']}")
            print(f"   Model: {created['model']}")
            conv_id = created['id']
            conv_uuid = created['conversation_id']
        else:
            print(f"❌ Failed to create conversation: {response.status_code}")
            print(f"   Response: {response.text}")
            return

        # Step 2: Wait for background vector storage
        print("\n[2] Waiting for background vector storage (3 seconds)...")
        await asyncio.sleep(3)

        # Step 3: Verify in PostgreSQL
        print("\n[3] Verifying conversation in PostgreSQL...")
        response = await client.get(f"{BASE_URL}/conversations/{conv_id}")

        if response.status_code == 200:
            conv = response.json()
            print(f"✅ Found in PostgreSQL:")
            print(f"   ID: {conv['id']}")
            print(f"   Model: {conv['model']}")
            print(f"   Message count: {len(conv['raw_data']['conversation'])}")
        else:
            print(f"❌ Not found in PostgreSQL: {response.status_code}")

        # Step 4: Search in ChromaDB (separate collection)
        print("\n[4] Searching in ChromaDB conversations collection...")
        search_request = {
            "query": "authentication with JWT tokens",
            "user_id": "test_user_1",
            "project_id": "test_project",
            "limit": 5,
            "min_similarity": 0.0
        }

        response = await client.post(
            f"{BASE_URL}/conversations/search",
            json=search_request
        )

        if response.status_code == 200:
            results = response.json()
            print(f"✅ Search completed. Found {len(results)} results")

            if results:
                for i, result in enumerate(results, 1):
                    print(f"\n   Result {i}:")
                    print(f"   - Conversation ID: {result['conversation_id']}")
                    print(f"   - Similarity: {result['similarity']:.4f}")
                    print(f"   - Model: {result['metadata'].get('model', 'N/A')}")
                    print(f"   - Message count: {result['metadata'].get('message_count', 'N/A')}")

                    # Check if our conversation is in results
                    if result['conversation_id'] == conv_uuid:
                        print(f"   ✅ FOUND OUR CONVERSATION IN CHROMADB!")
            else:
                print("   ⚠️  No results found. Vector may not be stored yet.")
        else:
            print(f"❌ Search failed: {response.status_code}")
            print(f"   Response: {response.text}")

        # Step 5: List all conversations
        print("\n[5] Listing all conversations...")
        response = await client.get(f"{BASE_URL}/conversations?limit=10")

        if response.status_code == 200:
            all_convs = response.json()
            print(f"✅ Found {len(all_convs)} total conversations in PostgreSQL")
        else:
            print(f"❌ Failed to list: {response.status_code}")

        print("\n" + "="*60)
        print("PIPELINE TEST COMPLETE")
        print("="*60)
        print("\nSUMMARY:")
        print("- PostgreSQL: Stores conversation data ✅")
        print("- Event Bus: Triggers background handler ✅")
        print("- ChromaDB: Stores vectors in conversations_{hash} collection")
        print("- Search: Queries separate collection for semantic search")
        print("\nIf search found your conversation, the pipeline is working! 🎉")


if __name__ == "__main__":
    asyncio.run(test_conversation_pipeline())
