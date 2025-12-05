import asyncio
import os
from dotenv import load_dotenv
from src.modules.llm.mistral_sdk.client import MistralClient

load_dotenv()

async def main():
    print("Testing Mistral Client...")
    
    try:
        client = MistralClient(model="mistral-medium-2508")
        response = await client.generate_content("Hello, tell me a short joke.")
        print(f"\nResponse:\n{response}")
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    asyncio.run(main())
