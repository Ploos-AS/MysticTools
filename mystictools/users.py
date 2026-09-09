from __future__ import annotations

import json
import os
from pathlib import Path

SCHEMA_VERSION = 1
DEFAULT_FILENAME = "mystictools-users.json"

SAFE_FIELDS = (
    "id",
    "handle",
    "security_level",
    "calls",
    "uploads",
    "downloads",
    "posts",
    "last_on",
)


def provider_path(root: Path) -> tuple[Path, str]:
    override = os.environ.get("MYSTICTOOLS_USER_SNAPSHOT")
    if override:
        path = Path(override)
        if not path.is_absolute():
            path = root / path
        return path, "environment"
    return root / DEFAULT_FILENAME, "sidecar-default"


def _normalize_user(record: object) -> dict | None:
    if not isinstance(record, dict):
        return None
    user_id = record.get("id")
    if not isinstance(user_id, int) or user_id < 1:
        return None
    normalized = {field: record.get(field) for field in SAFE_FIELDS}
    normalized["id"] = user_id
    return normalized


def users_snapshot(root: Path) -> dict:
    path, source = provider_path(root)
    if not path.is_file():
        return {
            "available": False,
            "qualified": False,
            "source": source,
            "path": str(path),
            "schema_version": None,
            "generated_at": None,
            "count": 0,
            "users": [],
            "error": None,
        }

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "available": True,
            "qualified": False,
            "source": source,
            "path": str(path),
            "schema_version": None,
            "generated_at": None,
            "count": 0,
            "users": [],
            "error": str(exc),
        }

    if payload.get("schema_version") != SCHEMA_VERSION or not isinstance(payload.get("users"), list):
        return {
            "available": True,
            "qualified": False,
            "source": source,
            "path": str(path),
            "schema_version": payload.get("schema_version"),
            "generated_at": payload.get("generated_at"),
            "count": 0,
            "users": [],
            "error": "unsupported or invalid users snapshot schema",
        }

    users = []
    invalid = 0
    for record in payload["users"]:
        normalized = _normalize_user(record)
        if normalized is None:
            invalid += 1
            continue
        users.append(normalized)

    users.sort(key=lambda item: item["id"])
    return {
        "available": True,
        "qualified": invalid == 0,
        "source": source,
        "path": str(path),
        "schema_version": SCHEMA_VERSION,
        "generated_at": payload.get("generated_at"),
        "count": len(users),
        "users": users,
        "error": f"{invalid} invalid user record(s)" if invalid else None,
    }
