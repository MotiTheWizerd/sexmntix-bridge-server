"""
Standalone runner for Intent ICM.

Usage examples (from repo root):
  $env:PYTHONPATH='.'; python scripts/test_icm_intent.py --text "what did we plan last week?"
  $env:PYTHONPATH='.'; python scripts/test_icm_intent.py --file sample.txt
"""
import argparse
import json
import sys
from typing import Optional

from src.modules.SXPrefrontal import ICMBrain


def classify_offline(text: str, context: Optional[str]) -> dict:
    """
    Deterministic, no-LLM intent classifier for testing.
    Keeps schema consistent with real ICM output.
    """
    lower = text.lower()
    intent = "unknown"
    route = "triage"
    required = []
    strategy = "none"

    if any(kw in lower for kw in ["what did", "what happened", "plan", "decide", "talk about", "yesterday"]):
        intent = "episodic_lookup"
        route = "retrieve"
        required = ["session_state", "conversation_history"]
        strategy = "recency"
    elif any(kw in lower for kw in ["who am i", "identity", "profile", "about me"]):
        intent = "identity_lookup"
        route = "retrieve"
        required = ["identity"]
        strategy = "identity"

    return {
        "intent": intent,
        "confidence": 0.82 if intent != "unknown" else 0.3,
        "confidence_reason": "offline heuristic",
        "route": route,
        "required_memory": required,
        "retrieval_strategy": strategy,
        "entities": [],
        "fallback": {
            "intent": "unknown",
            "route": "triage",
        },
        "notes": "offline mode: no LLM call",
    }


def payload_size_bytes(data) -> int:
    return len(json.dumps(data, ensure_ascii=True))


def read_text(args: argparse.Namespace) -> str:
    if args.text:
        return args.text
    if args.file:
        return open(args.file, "r", encoding="utf-8").read()
    return sys.stdin.read()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Intent ICM on a single input.")
    parser.add_argument("--text", type=str, help="Inline text to classify.")
    parser.add_argument("--file", type=str, help="Path to file containing input text.")
    parser.add_argument("--context", type=str, default=None, help="Optional context string.")
    parser.add_argument("--offline", action="store_true", help="Use deterministic offline heuristics (no LLM).")
    return parser.parse_args()


def main():
    args = parse_args()
    text = read_text(args).strip()
    if not text:
        print("No input provided.")
        sys.exit(1)

    if args.offline:
        result = classify_offline(text, context=args.context)
    else:
        icm = ICMBrain()
        result = icm.classify(text, context=args.context)

    print("Intent ICM result:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"\nPayload bytes: {payload_size_bytes(result)}")


if __name__ == "__main__":
    main()
