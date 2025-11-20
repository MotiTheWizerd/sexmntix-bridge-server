"""
Migration helper to reshape memory/mental note JSON files and move them into
the new project-scoped directory layout:

data/users/user_<user_id>/project_<project_id>/{memory_logs, mental_notes}

Rules:
- user_id is fixed to the provided constant (from CLI or default below).
- project_id is set to "semntix-code" by default.
- session_id is set to "000-000-000-000" if missing.
- datetime: derived from the memory_log.date (or mental note startTime/date) if missing,
  using midnight ISO format.
- Memory logs: if not already wrapped, wrap into:
    {
      "user_id": ...,
      "project_id": ...,
      "session_id": ...,
      "datetime": ...,
      "memory_log": { ...existing fields... }
    }
- Mental notes: keep payload as-is but ensure user_id/project_id/sessionId/startTime are present;
  do not otherwise modify content fields.

The script defaults to a dry run. Pass --apply to write changes.
"""

import argparse
import json
import shutil
from dataclasses import dataclass
from datetime import datetime, date
from pathlib import Path
from typing import Any, Dict, Tuple

# Defaults provided by the user request
DEFAULT_USER_ID = "84e17260-ff03-409b-bf30-0b5ba52a2ab4"
DEFAULT_PROJECT_ID = "semntix-code"
DEFAULT_SESSION_ID = "000-000-000-000"


@dataclass
class MigrationConfig:
    base_dir: Path  # destination base (data/users/user_<id>)
    source_dir: Path  # source root (data/memory_logs_migrate)
    user_id: str
    project_id: str
    session_id: str
    apply: bool
    backup: bool


def parse_args() -> MigrationConfig:
    parser = argparse.ArgumentParser(description="Migrate memory/mental note JSON files.")
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=Path("data") / "users" / f"user_{DEFAULT_USER_ID}",
        help="Destination base directory (data/users/user_<id>).",
    )
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=Path("data") / "memory_logs_migrate",
        help="Source directory containing memory_logs/ and mental_notes/ JSON files to migrate.",
    )
    parser.add_argument("--user-id", default=DEFAULT_USER_ID, help="User ID to set in payloads.")
    parser.add_argument("--project-id", default=DEFAULT_PROJECT_ID, help="Project ID to set in payloads.")
    parser.add_argument("--session-id", default=DEFAULT_SESSION_ID, help="Session ID to set if missing.")
    parser.add_argument(
        "--apply", action="store_true", help="Apply changes (default is dry run)."
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Copy original files to *.bak alongside writes (only when --apply).",
    )
    args = parser.parse_args()
    return MigrationConfig(
        base_dir=args.base_dir,
        source_dir=args.source_dir,
        user_id=args.user_id,
        project_id=args.project_id,
        session_id=args.session_id,
        apply=args.apply,
        backup=args.backup,
    )


def safe_load_json(path: Path) -> Tuple[Dict[str, Any], bool]:
    with path.open("r", encoding="utf-8") as f:
        content = json.load(f)
    return content, True


def ensure_datetime_from_date(date_value: Any) -> str:
    """
    Convert date-like values to ISO datetime with midnight time.
    Falls back to now() if parsing fails.
    """
    if isinstance(date_value, datetime):
        return date_value.isoformat()
    if isinstance(date_value, date):
        return datetime.combine(date_value, datetime.min.time()).isoformat()
    if isinstance(date_value, str):
        for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
            try:
                dt = datetime.strptime(date_value, fmt)
                return dt.isoformat()
            except ValueError:
                continue
        try:
            return datetime.fromisoformat(date_value.replace("Z", "+00:00")).isoformat()
        except ValueError:
            pass
    return datetime.utcnow().isoformat()


def migrate_memory_log(
    payload: Dict[str, Any], cfg: MigrationConfig
) -> Dict[str, Any]:
    """
    Wrap/normalize memory log payload.
    """
    if "memory_log" in payload and isinstance(payload["memory_log"], dict):
        memory_log = payload["memory_log"]
    else:
        memory_log = dict(payload)

    memory_log.setdefault("task", "unknown")
    memory_log.setdefault("agent", "unknown")

    date_value = (
        memory_log.get("date")
        or payload.get("date")
    )
    datetime_iso = payload.get("datetime") or ensure_datetime_from_date(date_value)

    wrapped = {
        "user_id": cfg.user_id,
        "project_id": cfg.project_id,
        "session_id": payload.get("session_id") or cfg.session_id,
        "datetime": datetime_iso,
        "memory_log": memory_log,
    }
    return wrapped


def migrate_mental_note(payload: Dict[str, Any], cfg: MigrationConfig) -> Dict[str, Any]:
    """
    Keep structure but ensure IDs/session/project are set. Minimal touch to avoid
    breaking schema assumptions elsewhere.
    """
    migrated = dict(payload)
    migrated["user_id"] = cfg.user_id
    migrated["project_id"] = cfg.project_id
    migrated["sessionId"] = migrated.get("sessionId") or cfg.session_id
    if "startTime" not in migrated:
        migrated["startTime"] = 0
    return migrated


def write_json(path: Path, data: Dict[str, Any], cfg: MigrationConfig) -> None:
    if cfg.apply:
        path.parent.mkdir(parents=True, exist_ok=True)
        if cfg.backup and path.exists():
            shutil.copy2(path, path.with_suffix(path.suffix + ".bak"))
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


def migrate_directory(cfg: MigrationConfig) -> None:
    # Support either structured input (memory_logs/, mental_notes/) or flat files in source_dir
    structured_memory = (cfg.source_dir / "memory_logs")
    structured_mental = (cfg.source_dir / "mental_notes")

    src_memory = structured_memory if structured_memory.exists() else cfg.source_dir
    src_mental = structured_mental if structured_mental.exists() else None  # skip if no mental_notes folder

    dest_base = cfg.base_dir / f"project_{cfg.project_id}"
    dest_memory = dest_base / "memory_logs"
    dest_mental = dest_base / "mental_notes"
    proceed_dir = cfg.source_dir / "proceed"
    proceed_memory = proceed_dir / "memory_logs"
    proceed_mental = proceed_dir / "mental_notes"

    memory_files = sorted(src_memory.glob("*.json")) if src_memory.exists() else []
    mental_files = sorted(src_mental.glob("*.json")) if src_mental and src_mental.exists() else []

    print(f"Memory logs found: {len(memory_files)}")
    print(f"Mental notes found: {len(mental_files)}")
    print(f"Destination: {dest_base}")
    print(f"Source: {cfg.source_dir}")
    print(f"Mode: {'APPLY' if cfg.apply else 'DRY-RUN'}")
    print()

    for path in memory_files:
        data, _ = safe_load_json(path)
        migrated = migrate_memory_log(data, cfg)
        dest_path = dest_memory / path.name
        print(f"[memory] {path} -> {dest_path}")
        write_json(dest_path, migrated, cfg)
        if cfg.apply:
            proceed_memory.mkdir(parents=True, exist_ok=True)
            shutil.move(str(path), proceed_memory / path.name)

    for path in mental_files:
        data, _ = safe_load_json(path)
        migrated = migrate_mental_note(data, cfg)
        dest_path = dest_mental / path.name
        print(f"[mental] {path} -> {dest_path}")
        write_json(dest_path, migrated, cfg)
        if cfg.apply:
            proceed_mental.mkdir(parents=True, exist_ok=True)
            shutil.move(str(path), proceed_mental / path.name)

    if not cfg.apply:
        print("\nDry run complete. Re-run with --apply to write changes.")
    else:
        print("\nMigration complete.")


def main() -> None:
    cfg = parse_args()
    migrate_directory(cfg)


if __name__ == "__main__":
    main()
