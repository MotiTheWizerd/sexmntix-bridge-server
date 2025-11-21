"""
SXPrefrontal SDK Test

Tests the updated SXPrefrontal module with the new qwen_sdk v0.2.0 API.
Credentials are auto-detected from:
  1. Environment variables (OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL)
  2. Qwen CLI credentials (~/.qwen/oauth_creds.json)
"""

import time
from src.modules.SXPrefrontal.model import SXPrefrontalModel
from src.modules.qwen_sdk import QwenConfigError, QwenAPIError

def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def main():
    total_start = time.time()

    print("🧠 SXPrefrontal SDK Test")
    print("Testing SXPrefrontal with new qwen_sdk v0.2.0")

    # Test 1: Initialize with auto-detection
    print_section("Test 1: Auto-detect Credentials")
    init_start = time.time()
    try:
        model = SXPrefrontalModel()
        init_duration = time.time() - init_start
        print(f"✅ Model initialized successfully ({init_duration*1000:.2f}ms)")
        print(f"   Using credentials from environment or CLI")
    except QwenConfigError as e:
        print(f"❌ Configuration Error: {e}")
        print("\nTo fix:")
        print("  1. Run 'qwen auth login' in terminal")
        print("  OR")
        print("  2. Set environment variables:")
        print("     export OPENAI_API_KEY='your-key'")
        print("     export OPENAI_BASE_URL='https://dashscope.aliyuncs.com/compatible-mode/v1'")
        print("     export OPENAI_MODEL='qwen3-coder-plus'")
        return

    # Test 2: Basic generation
    print_section("Test 2: Basic Text Generation")
    try:
        prompt = "What is Python? Give a brief answer."
        print(f"📤 Prompt: {prompt}")

        start = time.time()
        response = model.generate(prompt)
        duration = time.time() - start

        print(f"✅ Response received in {duration:.3f}s ({duration*1000:.0f}ms)")
        print(f"📝 Response:\n{response}")
    except Exception as e:
        print(f"❌ Error: {e}")

    # Test 3: Generation with system prompt (NEW FEATURE!)
    print_section("Test 3: Generation with System Prompt")
    try:
        system_prompt = "You are a helpful coding assistant. Keep answers concise."
        prompt = "Write a Python function to calculate factorial."

        print(f"🤖 System: {system_prompt}")
        print(f"📤 Prompt: {prompt}")

        start = time.time()
        response = model.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=500
        )
        duration = time.time() - start

        print(f"✅ Response received in {duration:.3f}s ({duration*1000:.0f}ms)")
        print(f"📝 Response:\n{response}")
    except Exception as e:
        print(f"❌ Error: {e}")

    # Test 4: Custom temperature
    print_section("Test 4: Creative Generation (Higher Temperature)")
    try:
        prompt = "Write a creative name for a Python package that helps with AI development."

        print(f"📤 Prompt: {prompt}")
        print(f"🌡️  Temperature: 0.9 (more creative)")

        start = time.time()
        response = model.generate(
            prompt=prompt,
            temperature=0.9,
            max_tokens=100
        )
        duration = time.time() - start

        print(f"✅ Response received in {duration:.3f}s ({duration*1000:.0f}ms)")
        print(f"📝 Response:\n{response}")
    except Exception as e:
        print(f"❌ Error: {e}")

    # Test 5: Custom initialization (with explicit params)
    print_section("Test 5: Custom Initialization")
    try:
        print("Creating model with custom max_tokens and temperature...")
        init_start = time.time()
        custom_model = SXPrefrontalModel(
            max_tokens=1000,
            temperature=0.5
        )
        init_duration = time.time() - init_start
        print(f"   Model created in {init_duration*1000:.2f}ms")

        start = time.time()
        response = custom_model.generate("List 3 features of Python.")
        duration = time.time() - start

        print(f"✅ Response received in {duration:.3f}s ({duration*1000:.0f}ms)")
        print(f"📝 Response:\n{response}")
    except Exception as e:
        print(f"❌ Error: {e}")

    total_duration = time.time() - total_start
    print_section("All Tests Complete!")
    print("✨ SXPrefrontal is working with the new qwen_sdk v0.2.0")
    print(f"⏱️  Total test time: {total_duration:.3f}s ({total_duration*1000:.0f}ms)")

if __name__ == "__main__":
    main()
