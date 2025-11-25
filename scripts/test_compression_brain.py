"""
Quick test runner for the CompressionBrain.

Usage:
  python scripts/test_compression_brain.py
  python scripts/test_compression_brain.py --user "..." --assistant "..."
"""

import argparse
import json

from src.modules.SXPrefrontal import CompressionBrain


def main():
    parser = argparse.ArgumentParser(description="Test CompressionBrain")
    parser.add_argument("--user", type=str, default=None, help="User text")
    parser.add_argument("--assistant", type=str, default=None, help="Assistant text")
    args = parser.parse_args()

    brain = CompressionBrain()

    samples = [
        (
            "Ray what was that bug in pgvector again? The one with metadata leaking? I think it broke last night.",
            "Yes, the bug was in the sanitize_filters function, where metadata wasn’t removed before vector search. It caused invalid retrieval. Fixed by reordering operations.",
        ),
        (
            "This answer is way too long and full of fluff. Can you summarize it?",
            "Absolutely — you’re 100% right... [long answer omitted]",
        ),
    ]

    pairs = (
        [(args.user, args.assistant)]
        if args.user or args.assistant
        else samples
    )

    for user_text, assistant_text in pairs:
        print("=" * 70)
        print("USER:", user_text)
        print("ASSISTANT:", assistant_text)
        result = brain.compress(user_text or "", assistant_text or "")
        print("COMPRESSED:", json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
