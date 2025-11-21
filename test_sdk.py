"""
Qwen SDK Test Page

This script demonstrates the Qwen SDK functionality.
It automatically detects your Qwen CLI credentials.
"""

import sys
from pathlib import Path
import time

# Add the SDK to the python path
# (In a real project, you would install the package via pip)
current_dir = Path(__file__).parent
sdk_path = current_dir / "src" / "modules" / "qwen-cli"
sys.path.insert(0, str(sdk_path))

try:
    from qwen_sdk import QwenClient, QwenConfigError
except ImportError:
    print("❌ Could not import qwen_sdk. Check the path.")
    sys.exit(1)

def main():
    print("🧪 Qwen SDK Test Page")
    print("====================")

    # 1. Initialize Client
    print("\n1. Initializing Client...")
    try:
        # This will automatically look for:
        # 1. Environment variables (OPENAI_API_KEY)
        # 2. Qwen CLI credentials (~/.qwen/oauth_creds.json)
        client = QwenClient()
        print("   ✅ Client initialized")
        
        # Show what auth method was found
        if client.api_key and client.api_key.startswith("sk-"):
            print("   🔑 Using API Key (from env/config)")
        else:
            print("   🔐 Using Qwen CLI Credentials (from ~/.qwen/oauth_creds.json)")
            
    except QwenConfigError as e:
        print(f"   ❌ Configuration Error: {e}")
        print("\n   To fix this:")
        print("   1. Run 'qwen auth login' in your terminal")
        print("   OR")
        print("   2. Set OPENAI_API_KEY environment variable")
        return

    # 2. Test Connection
    print("\n2. Testing Connection (Simple Query)...")
    start_time = time.time()
    try:
        response = client.ask("Hello! Just saying hi to test the connection.")
        duration = time.time() - start_time
        print(f"   ✅ Response received in {duration:.2f}s")
        print(f"   📝 Output: {response}")
    except Exception as e:
        print(f"   ❌ Request Failed: {e}")
        return

    # 3. Test Code Generation
    print("\n3. Testing Code Generation...")
    try:
        prompt = "Write a Python function to calculate the factorial of a number."
        print(f"   📤 Prompt: {prompt}")
        
        start_time = time.time()
        response = client.ask(prompt, max_tokens=500)
        duration = time.time() - start_time
        
        print(f"   ✅ Response received in {duration:.2f}s")
        print("   📝 Output:")
        print("-" * 40)
        print(response)
        print("-" * 40)
    except Exception as e:
        print(f"   ❌ Request Failed: {e}")

if __name__ == "__main__":
    main()
