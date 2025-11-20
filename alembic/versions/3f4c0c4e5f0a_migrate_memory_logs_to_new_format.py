"""migrate_memory_logs_to_new_format

Revision ID: 3f4c0c4e5f0a
Revises: 0262664a5929
Create Date: 2025-11-20 01:55:00.000000

"""
from typing import Sequence, Union, Any, Dict
from datetime import datetime, date

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "3f4c0c4e5f0a"
down_revision: Union[str, None] = "0262664a5929"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Table helper
memory_logs = sa.table(
    "memory_logs",
    sa.column("id", sa.String()),
    sa.column("task", sa.String()),
    sa.column("agent", sa.String()),
    sa.column("date", sa.DateTime()),
    sa.column("raw_data", postgresql.JSONB(astext_type=sa.Text())),
    sa.column("user_id", sa.String()),
    sa.column("project_id", sa.String()),
    sa.column("created_at", sa.DateTime()),
)


def _parse_date(value: Any) -> date:
    """Best-effort conversion to date for temporal_context and date string."""
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        for fmt in ("%Y-%m-%d",):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
        except ValueError:
            pass
    # Fallback to today if parsing fails
    return datetime.utcnow().date()


def _calculate_temporal_context(dt_value: date) -> Dict[str, Any]:
    """Replicates TemporalContextCalculator without importing application code."""
    year = dt_value.year
    month = dt_value.month
    week_number = dt_value.isocalendar()[1]
    quarter = (month - 1) // 3 + 1

    days_diff = (date.today() - dt_value).days
    if days_diff < 7:
        time_period = "recent"
    elif days_diff < 14:
        time_period = "last-week"
    elif days_diff < 30:
        time_period = "last-month"
    else:
        time_period = "archived"

    return {
        "date_iso": dt_value.isoformat(),
        "year": year,
        "month": month,
        "week_number": week_number,
        "quarter": f"{year}-Q{quarter}",
        "time_period": time_period,
    }


def _normalize_tags(memory_log: Dict[str, Any], legacy_raw: Dict[str, Any]) -> None:
    """Ensure tags are stored as a simple list."""
    tags = memory_log.get("tags")
    normalized = None

    if isinstance(tags, list):
        normalized = [str(tag) for tag in tags if tag is not None]
    elif isinstance(tags, dict):
        normalized = [
            str(value)
            for key, value in tags.items()
            if key.startswith("tag_") and value is not None
        ]
    elif isinstance(legacy_raw, dict):
        legacy_tags = [
            str(value)
            for key, value in legacy_raw.items()
            if key.startswith("tag_") and value is not None
        ]
        normalized = legacy_tags or None

    if normalized:
        memory_log["tags"] = normalized
    elif "tags" in memory_log and not normalized:
        # Remove empty/invalid tags to avoid storing nulls
        memory_log.pop("tags", None)


def _build_memory_log_payload(row, raw_data: Any) -> Dict[str, Any]:
    """Transform legacy raw_data blobs into the new structured format."""
    # If already migrated, return as-is
    if isinstance(raw_data, dict) and "memory_log" in raw_data:
        return raw_data

    # Extract legacy payload
    if isinstance(raw_data, dict):
        memory_log_data = dict(raw_data)
        # Drop potential top-level fields that now live above memory_log
        for key in ["user_id", "project_id", "session_id", "datetime", "memory_log_id"]:
            memory_log_data.pop(key, None)
    else:
        memory_log_data = {}
        if raw_data not in (None, ""):
            # Preserve non-dict blobs as legacy content
            memory_log_data["content"] = raw_data

    # Required fields with fallbacks
    if not memory_log_data.get("task"):
        memory_log_data["task"] = row.task or "unknown"
    if not memory_log_data.get("agent"):
        memory_log_data["agent"] = row.agent or "unknown"

    # Normalize date field to ISO string
    date_value = memory_log_data.get("date") or row.date
    parsed_date = _parse_date(date_value or row.created_at or datetime.utcnow())
    memory_log_data["date"] = parsed_date.isoformat()

    # Ensure temporal_context exists
    if not memory_log_data.get("temporal_context"):
        memory_log_data["temporal_context"] = _calculate_temporal_context(parsed_date)

    # Normalize tags into list form
    _normalize_tags(memory_log_data, raw_data if isinstance(raw_data, dict) else {})

    # Session/datetime handling
    session_id = raw_data.get("session_id") if isinstance(raw_data, dict) else None
    datetime_iso = None
    if isinstance(raw_data, dict):
        datetime_iso = raw_data.get("datetime")
    if not datetime_iso:
        datetime_iso = (
            row.created_at.isoformat()
            if isinstance(row.created_at, datetime)
            else datetime.utcnow().isoformat()
        )

    return {
        "user_id": str(row.user_id) if row.user_id is not None else None,
        "project_id": row.project_id or "default",
        "session_id": session_id,
        "datetime": datetime_iso,
        "memory_log": memory_log_data,
    }


def upgrade() -> None:
    """
    Wrap legacy memory_logs.raw_data into the new structured format:
    {
        "user_id": ...,
        "project_id": ...,
        "session_id": ...,
        "datetime": ...,
        "memory_log": { ... detailed fields ... }
    }
    """
    conn = op.get_bind()
    rows = conn.execute(
        sa.select(
            memory_logs.c.id,
            memory_logs.c.task,
            memory_logs.c.agent,
            memory_logs.c.date,
            memory_logs.c.raw_data,
            memory_logs.c.user_id,
            memory_logs.c.project_id,
            memory_logs.c.created_at,
        )
    ).fetchall()

    for row in rows:
        new_payload = _build_memory_log_payload(row, row.raw_data)
        # Skip if nothing changed
        if new_payload == row.raw_data:
            continue

        conn.execute(
            sa.update(memory_logs)
            .where(memory_logs.c.id == row.id)
            .values(raw_data=new_payload)
        )


def downgrade() -> None:
    """Flatten memory_logs.raw_data back to legacy shape by dropping the wrapper."""
    conn = op.get_bind()
    rows = conn.execute(
        sa.select(memory_logs.c.id, memory_logs.c.raw_data)
    ).fetchall()

    for row in rows:
        raw_data = row.raw_data
        if isinstance(raw_data, dict) and "memory_log" in raw_data:
            flattened = dict(raw_data["memory_log"])
        else:
            flattened = raw_data

        conn.execute(
            sa.update(memory_logs)
            .where(memory_logs.c.id == row.id)
            .values(raw_data=flattened)
        )
