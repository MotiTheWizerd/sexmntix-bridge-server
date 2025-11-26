from datetime import datetime, timezone
from typing import Any, Optional

def resolve_time_window(time_icm, time_text: Optional[str], now: Optional[datetime], tz_offset_minutes: Optional[int]):
    """
    Resolve time window using TimeICMBrain when no explicit window is provided.
    """
    if (time_text is None) or (time_icm is None):
        return None, None, None
    time_result = time_icm.resolve(
        time_text,
        now=now or datetime.now(timezone.utc),
        tz_offset_minutes=tz_offset_minutes,
    )
    start_time = parse_iso(time_result.get("start_time"))
    end_time = parse_iso(time_result.get("end_time"))
    return time_result, to_naive_utc(start_time), to_naive_utc(end_time)


def parse_iso(value: Any) -> Optional[datetime]:
    if not value or not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def to_naive_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Convert an aware datetime to naive UTC (tzinfo stripped) to match TIMESTAMP WITHOUT TIME ZONE.
    """
    if dt is None:
        return None
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt
