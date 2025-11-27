from typing import Dict, Any
from rich.console import Console


console = Console()


def log_fetch_memory_state(world_view: Dict[str, Any] | None, identity: Dict[str, Any] | None, results: list, prompt: str, inject_world_view: bool) -> None:
    """
    Centralized logging for fetch-memory orchestration to keep the router lean.
    """
    console.log(
        "[world-view-injection] pipeline completed",
        {
            "world_view_present": bool(world_view),
            "world_view_injected": bool(inject_world_view and world_view),
            "has_short_term": bool(world_view and world_view.get("short_term_memory")),
            "world_view_cached": bool(world_view and world_view.get("is_cached")),
            "recent_conversations": len(world_view.get("recent_conversations", [])) if isinstance(world_view, dict) else 0,
            "results_count": len(results or []),
            "identity_present": bool(identity),
        },
    )

    console.log(
        "[world-view-injection] prompt built",
        {
            "prompt_length": len(prompt or ""),
            "includes_short_term": bool(
                world_view
                and isinstance(world_view, dict)
                and world_view.get("short_term_memory")
                and world_view.get("short_term_memory") in prompt
            ),
            "includes_identity": bool(identity and isinstance(identity, dict) and identity.get("user_identity")),
            "includes_recent_conversations": bool(
                inject_world_view
                and world_view
                and isinstance(world_view, dict)
                and world_view.get("recent_conversations")
                and any(world_view.get("recent_conversations"))
            ),
        },
    )
