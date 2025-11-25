"""
Quick test runner for the ICM intent classifier.

Usage:
  python scripts/test_icm_brain.py

Ensure env vars (OPENAI_API_KEY/OPENAI_BASE_URL/OPENAI_MODEL) are set for Qwen-compatible API.
"""

import json
from typing import List

from src.modules.SXPrefrontal import ICMBrain


def run_samples(samples: List[str], context: str | None = None):
    brain = ICMBrain()
    for text in samples:
        result = brain.classify(text, context=context)
        print("User:", text)
        print(json.dumps(result, indent=2))
        print("-" * 40)


if __name__ == "__main__":
    SAMPLE_CONTEXT = "Channel: web; Session: demo; App: semantix-bridge"
    SAMPLE_UTTERANCES = [
        "Can you summarize our authentication plans from last week?",
        "hi",
        "not sure what happened, it broke again",
        "Book a meeting with the infra team tomorrow",
    ]
    run_samples(SAMPLE_UTTERANCES, context=SAMPLE_CONTEXT)
