"""
Test runner for TimeICMBrain.

Usage:
  python scripts/test_time_icm.py
  python scripts/test_time_icm.py --text "last night" --now "2025-11-25T10:00:00Z" --tz-offset 0
"""

import argparse
import json
from datetime import datetime, timezone

from src.modules.SXPrefrontal import TimeICMBrain


def parse_now(value: str | None) -> datetime | None:
    if not value:
        return None
    # Allow 'Z'
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


def main():
    parser = argparse.ArgumentParser(description="Test TimeICMBrain")
    parser.add_argument("--text", type=str, default=None, help="Time expression text")
    parser.add_argument("--now", type=str, default=None, help="Override now in ISO format (e.g., 2025-11-25T10:00:00Z)")
    parser.add_argument("--tz-offset", type=int, default=None, help="Timezone offset minutes (e.g., 120 for UTC+2)")
    parser.add_argument("--provider", type=str, default="mistral", help="LLM provider (mistral, qwen, gemini)")
    parser.add_argument("--model", type=str, default=None, help="Model name (e.g., mistral-tiny)")
    args = parser.parse_args()

    from src.modules.SXPrefrontal.model import SXPrefrontalModel
    model = SXPrefrontalModel(provider=args.provider, model=args.model)
    brain = TimeICMBrain(model=model)
    now = parse_now(args.now) or datetime.now(timezone.utc)

    samples = [
        "last night",
        "yesterday at 3pm",
        "last 2 hours",
        "tomorrow morning",
        "between 3pm and 5pm",
        "this week",
        "last week",
        "2 days ago",
    ]

    tests = [args.text] if args.text else samples

    print(f"Testing Time ICM with provider: {args.provider}, model: {args.model or 'default'}")
    print("=" * 70)

    for text in tests:
        print("=" * 70)
        print("Text:", text)
        result = brain.resolve(text, now=now, tz_offset_minutes=args.tz_offset)
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
