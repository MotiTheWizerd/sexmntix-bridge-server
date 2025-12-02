"""
Test harness for fan-out ICM execution with an event collector.

It simulates `message.received` -> multiple ICM handlers -> collector merge,
and reports payload sizes so we can see how much each stage carries.
"""
import argparse
import asyncio
import json
import time
import uuid
from typing import Any, Dict, Iterable, List, Set

from src.modules.core import EventBus


def build_message(payload_bytes: int) -> str:
    """
    Create synthetic text roughly payload_bytes long.
    """
    seed = "user message content "
    repeats = max(1, payload_bytes // len(seed) + 1)
    text = (seed * repeats)[:payload_bytes]
    return text


def payload_size_bytes(data: Any) -> int:
    return len(json.dumps(data, ensure_ascii=True))


class ICMCollector:
    """
    Collects icm.result events until the expected set arrives or timeout hits.
    """

    def __init__(self, bus: EventBus, expected_icms: Iterable[str]):
        self.bus = bus
        self.expected: Set[str] = set(expected_icms)
        self.results: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self.events: Dict[str, asyncio.Event] = {}
        self.bus.subscribe("icm.result", self._on_result)

    async def _on_result(self, payload: Dict[str, Any]):
        cid = payload["correlation_id"]
        icm = payload["icm"]
        state = self.results.setdefault(cid, {})
        state[icm] = payload
        event = self.events.setdefault(cid, asyncio.Event())
        if self.expected.issubset(state.keys()):
            event.set()

    async def wait_for(self, correlation_id: str, timeout: float) -> Dict[str, Any]:
        event = self.events.setdefault(correlation_id, asyncio.Event())
        try:
            await asyncio.wait_for(event.wait(), timeout)
        except asyncio.TimeoutError:
            pass
        return self.results.get(correlation_id, {})


def make_icm_handler(
    bus: EventBus,
    name: str,
    world_view_bytes: int,
    identity_bytes: int,
) -> Any:
    async def handler(event: Dict[str, Any]):
        started = time.perf_counter()
        message = event["message"]
        if name == "intent":
            data = {
                "intent": "mock_intent",
                "route": "triage",
                "required_memory": ["session_state"],
            }
        elif name == "time":
            data = {
                "start_time": None,
                "end_time": None,
                "resolution_confidence": 0.0,
                "notes": "stubbed",
            }
        elif name == "identity":
            filler = ("identity-" * 16)[: identity_bytes or 0]
            data = {"user_id": event["user_id"], "project_id": event["project_id"], "blob": filler}
        elif name == "world_view":
            data = {"world_view": ("world-view-" * 16)[: world_view_bytes or 0]}
        else:
            data = {"info": f"unhandled icm {name}"}

        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        bus.publish(
            "icm.result",
            {
                "icm": name,
                "correlation_id": event["correlation_id"],
                "duration_ms": elapsed_ms,
                "payload": data,
                "payload_bytes": payload_size_bytes(data),
                "message_bytes": len(message),
            },
        )

    return handler


async def run_once(
    message_bytes: int,
    icms: List[str],
    world_view_bytes: int,
    identity_bytes: int,
    timeout: float,
):
    bus = EventBus()
    collector = ICMCollector(bus, icms)

    for icm in icms:
        bus.subscribe(
            "message.received",
            make_icm_handler(
                bus=bus,
                name=icm,
                world_view_bytes=world_view_bytes,
                identity_bytes=identity_bytes,
            ),
        )

    correlation_id = str(uuid.uuid4())
    message_text = build_message(message_bytes)
    event = {
        "correlation_id": correlation_id,
        "message": message_text,
        "user_id": "test-user",
        "project_id": "test-project",
    }

    print(f"Publishing message.received with ~{len(message_text)} bytes")
    bus.publish("message.received", event)

    results = await collector.wait_for(correlation_id, timeout=timeout)
    missing = set(icms) - set(results.keys())
    if missing:
        print(f"Timed out waiting for: {', '.join(sorted(missing))}")

    print("\nICM results:")
    for name, payload in sorted(results.items()):
        print(
            f"- {name:10s} | payload_bytes={payload['payload_bytes']}, "
            f"duration_ms={payload['duration_ms']}"
        )

    merged = {name: payload["payload"] for name, payload in results.items()}
    print(f"\nCollector merged payload bytes: {payload_size_bytes(merged)}")
    print(f"Message bytes carried through handlers: {len(message_text)}")


def parse_icms(raw: str) -> List[str]:
    return [part.strip() for part in raw.split(",") if part.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Test ICM fan-out and collector sizing.")
    parser.add_argument("--message-bytes", type=int, default=80000, help="Approx size of synthetic message text.")
    parser.add_argument(
        "--icms",
        type=parse_icms,
        default=["intent", "time", "identity", "world_view"],
        help="Comma-separated list of ICMs to simulate.",
    )
    parser.add_argument(
        "--world-view-bytes",
        type=int,
        default=20000,
        help="Size of stubbed world view payload to mimic heavy data.",
    )
    parser.add_argument(
        "--identity-bytes",
        type=int,
        default=8000,
        help="Size of stubbed identity payload segment.",
    )
    parser.add_argument("--timeout", type=float, default=5.0, help="Seconds to wait for ICM results.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(
        run_once(
            message_bytes=args.message_bytes,
            icms=args.icms,
            world_view_bytes=args.world_view_bytes,
            identity_bytes=args.identity_bytes,
            timeout=args.timeout,
        )
    )
