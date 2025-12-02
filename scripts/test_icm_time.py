"""
Standalone runner for Time ICM.

Usage examples (from repo root):
  $env:PYTHONPATH='.'; python scripts/test_icm_time.py --text "what did we decide yesterday?"
  $env:PYTHONPATH='.'; python scripts/test_icm_time.py --text "show me last Monday" --tz-offset 120
"""
import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from typing import Optional

from src.modules.SXPrefrontal import TimeICMBrain


def _to_tz(dt: datetime, tz_offset_minutes: Optional[int]) -> datetime:
    if tz_offset_minutes is None:
        return dt
    tz = timezone(timedelta(minutes=tz_offset_minutes))
    return dt.astimezone(tz)


def _yesterday_window(now: datetime, tz_offset_minutes: Optional[int]) -> tuple[str, str]:
    local_now = _to_tz(now, tz_offset_minutes)
    start_local = local_now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
    end_local = start_local + timedelta(days=1)
    return start_local.astimezone(timezone.utc).isoformat(), end_local.astimezone(timezone.utc).isoformat()


def _last_week_window(now: datetime, tz_offset_minutes: Optional[int]) -> tuple[str, str]:
    local_now = _to_tz(now, tz_offset_minutes)
    start_local = local_now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=7)
    end_local = local_now.replace(hour=23, minute=59, second=59, microsecond=0)
    return start_local.astimezone(timezone.utc).isoformat(), end_local.astimezone(timezone.utc).isoformat()


def resolve_offline(text: str, now: datetime, tz_offset_minutes: Optional[int]) -> dict:
    lower = text.lower()
    start_iso = None
    end_iso = None
    granularity = "unknown"
    notes = "offline heuristic"

    if "yesterday" in lower:
        start_iso, end_iso = _yesterday_window(now, tz_offset_minutes)
        granularity = "day"
    elif "last week" in lower or "past week" in lower:
        start_iso, end_iso = _last_week_window(now, tz_offset_minutes)
        granularity = "week"

    return {
        "time_expression": text.strip(),
        "start_time": start_iso,
        "end_time": end_iso,
        "resolution_confidence": 0.8 if start_iso else 0.3,
        "granularity": granularity,
        "notes": notes,
    }


def payload_size_bytes(data) -> int:
    return len(json.dumps(data, ensure_ascii=True))


def read_text(args: argparse.Namespace) -> str:
    if args.text:
        return args.text
    if args.file:
        return open(args.file, "r", encoding="utf-8").read()
    return sys.stdin.read()


def parse_iso_datetime(value: str) -> datetime:
    cleaned = value.strip()
    if cleaned.endswith("Z"):
        cleaned = cleaned.replace("Z", "+00:00")
    dt = datetime.fromisoformat(cleaned)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Time ICM on a single input.")
    parser.add_argument("--text", type=str, help="Inline text to resolve.")
    parser.add_argument("--file", type=str, help="Path to file containing input text.")
    parser.add_argument("--tz-offset", type=int, default=None, help="Timezone offset minutes (e.g., 120 for UTC+2).")
    parser.add_argument("--now", type=str, default=None, help="Reference time in ISO format (e.g., 2025-11-30T01:46:00Z).")
    parser.add_argument("--offline", action="store_true", help="Use deterministic offline heuristics (no LLM).")
    parser.add_argument("--debug", action="store_true", help="Show raw LLM output and prompts.")
    return parser.parse_args()


def main():
    args = parse_args()
    text = read_text(args).strip()
    if not text:
        print("No input provided.")
        sys.exit(1)

    now = parse_iso_datetime(args.now) if args.now else datetime.now(timezone.utc)
    if args.offline:
        result = resolve_offline(text, now=now, tz_offset_minutes=args.tz_offset)
    else:
        brain = TimeICMBrain()
        result = brain.resolve(text, now=now, tz_offset_minutes=args.tz_offset, debug=args.debug)

    print("Time ICM result:")
    print(json.dumps(result, indent=2, ensure_ascii=True))
    print(f"\nPayload bytes: {payload_size_bytes(result)}")


if __name__ == "__main__":
    main()
