from __future__ import annotations

import json
import os
import time
from pathlib import Path

SCHEMA_VERSION = 1
DEFAULT_FILENAME = "mystictools-users.json"
DEFAULT_MAX_AGE_SECONDS = 900
DEFAULT_FUTURE_SKEW_SECONDS = 5

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
NUMERIC_FIELDS = ("security_level", "calls", "uploads", "downloads", "posts")


def provider_path(root: Path) -> tuple[Path, str]:
    override = os.environ.get("MYSTICTOOLS_USER_SNAPSHOT")
    if override:
        path = Path(override)
        if not path.is_absolute():
            path = root / path
        return path, "environment"
    return root / DEFAULT_FILENAME, "sidecar-default"


def max_age_seconds() -> int:
    value = os.environ.get("MYSTICTOOLS_USER_MAX_AGE")
    if value is None:
        return DEFAULT_MAX_AGE_SECONDS
    try:
        parsed = int(value)
    except ValueError:
        return DEFAULT_MAX_AGE_SECONDS
    return max(1, parsed)


def _normalize_user(record: object) -> tuple[dict | None, str | None]:
    if not isinstance(record, dict):
        return None, "not an object"
    user_id = record.get("id")
    if not isinstance(user_id, int) or isinstance(user_id, bool) or user_id < 1:
        return None, "invalid id"
    handle = record.get("handle")
    if handle is not None and not isinstance(handle, str):
        return None, f"user {user_id}: invalid handle type"
    last_on = record.get("last_on")
    if last_on is not None and not isinstance(last_on, (str, int, float)):
        return None, f"user {user_id}: invalid last_on type"
    normalized = {field: record.get(field) for field in SAFE_FIELDS}
    normalized["id"] = user_id
    for field in NUMERIC_FIELDS:
        value = normalized.get(field)
        if value is not None and (not isinstance(value, int) or isinstance(value, bool) or value < 0):
            return None, f"user {user_id}: invalid {field}"
    return normalized, None


def users_snapshot(root: Path, now: float | None = None) -> dict:
    path, source = provider_path(root)
    maximum_age = max_age_seconds()
    current_time = time.time() if now is None else now
    base = {
        "source": source,
        "path": str(path),
        "max_age_seconds": maximum_age,
        "age_seconds": None,
        "fresh": False,
        "complete_scan": False,
        "max_user_id_scanned": None,
    }
    if not path.is_file():
        return {
            **base,
            "available": False,
            "qualified": False,
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
            **base,
            "available": True,
            "qualified": False,
            "schema_version": None,
            "generated_at": None,
            "count": 0,
            "users": [],
            "error": str(exc),
        }

    if not isinstance(payload, dict) or payload.get("schema_version") != SCHEMA_VERSION or not isinstance(payload.get("users"), list):
        return {
            **base,
            "available": True,
            "qualified": False,
            "schema_version": payload.get("schema_version") if isinstance(payload, dict) else None,
            "generated_at": payload.get("generated_at") if isinstance(payload, dict) else None,
            "count": 0,
            "users": [],
            "error": "unsupported or invalid users snapshot schema",
        }

    errors: list[str] = []
    generated_at = payload.get("generated_at")
    age_seconds: int | None = None
    fresh = False
    if not isinstance(generated_at, (int, float)) or isinstance(generated_at, bool):
        errors.append("missing or invalid generated_at")
    else:
        delta = current_time - float(generated_at)
        if delta < -DEFAULT_FUTURE_SKEW_SECONDS:
            errors.append("generated_at is in the future")
        else:
            age_seconds = int(max(0.0, delta))
            fresh = age_seconds <= maximum_age
            if not fresh:
                errors.append("users snapshot is stale")

    max_user_id_scanned = payload.get("max_user_id_scanned")
    complete_scan = isinstance(max_user_id_scanned, int) and not isinstance(max_user_id_scanned, bool) and max_user_id_scanned >= 1
    if not complete_scan:
        errors.append("missing or invalid max_user_id_scanned")

    users: list[dict] = []
    seen: set[int] = set()
    for index, record in enumerate(payload["users"]):
        normalized, error = _normalize_user(record)
        if error is not None or normalized is None:
            errors.append(error or f"record {index}: invalid")
            continue
        if normalized["id"] in seen:
            errors.append(f"duplicate user id: {normalized['id']}")
            continue
        seen.add(normalized["id"])
        if complete_scan and normalized["id"] > max_user_id_scanned:
            errors.append(f"user id exceeds max_user_id_scanned: {normalized['id']}")
            continue
        users.append(normalized)

    users.sort(key=lambda item: item["id"])
    return {
        **base,
        "available": True,
        "qualified": not errors,
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "age_seconds": age_seconds,
        "fresh": fresh,
        "complete_scan": complete_scan,
        "max_user_id_scanned": max_user_id_scanned if complete_scan else None,
        "count": len(users),
        "users": users,
        "error": "; ".join(errors) if errors else None,
    }
