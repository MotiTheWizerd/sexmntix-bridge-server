"""
Standalone runner for Identity ICM service.

Usage examples (from repo root):
  $env:PYTHONPATH='.'; python scripts/test_icm_identity.py --user user-123 --project proj-abc
"""
import argparse
import json

from src.services.identity_service import IdentityICMService
from src.modules.core.telemetry.logger import get_logger


def payload_size_bytes(data) -> int:
    return len(json.dumps(data, ensure_ascii=True))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch identity payload for a user/project.")
    parser.add_argument("--user", type=str, default=None, help="User ID")
    parser.add_argument("--project", type=str, default=None, help="Project ID")
    return parser.parse_args()


def main():
    args = parse_args()
    service = IdentityICMService(logger=get_logger(__name__))
    payload = service.get_identity(user_id=args.user, project_id=args.project)

    print("Identity payload:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    print(f"\nPayload bytes: {payload_size_bytes(payload)}")


if __name__ == "__main__":
    main()
