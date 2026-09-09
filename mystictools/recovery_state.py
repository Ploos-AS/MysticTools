from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path

SCHEMA_VERSION = 1


def state_path(root: Path) -> Path:
    root = root.resolve()
    override = os.environ.get("MYSTICTOOLS_RECOVERY_STATE")
    if override:
        path = Path(override).expanduser()
        return path if path.is_absolute() else root.parent / path
    return root.parent / f".{root.name}.mystictools-recovery.json"


def record_event(root: Path, operation: str, success: bool, **details) -> None:
    path = state_path(root)
    payload = read_state(root)["state"] or {"schema_version": SCHEMA_VERSION, "events": {}}
    payload["schema_version"] = SCHEMA_VERSION
    payload.setdefault("events", {})[operation] = {
        "timestamp": int(time.time()),
        "success": bool(success),
        **{key: value for key, value in details.items() if value is not None},
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def safe_record_event(root: Path, operation: str, success: bool, **details) -> bool:
    try:
        record_event(root, operation, success, **details)
        return True
    except (OSError, TypeError, ValueError):
        return False


def read_state(root: Path, now: int | None = None) -> dict:
    path = state_path(root)
    if not path.is_file():
        return {"available": False, "qualified": False, "path": str(path), "state": None, "ages": {}, "error": None}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"available": True, "qualified": False, "path": str(path), "state": None, "ages": {}, "error": str(exc)}
    if not isinstance(payload, dict) or payload.get("schema_version") != SCHEMA_VERSION or not isinstance(payload.get("events", {}), dict):
        return {"available": True, "qualified": False, "path": str(path), "state": None, "ages": {}, "error": "invalid recovery state schema"}
    current = int(time.time()) if now is None else int(now)
    ages = {}
    for name, event in payload.get("events", {}).items():
        if isinstance(event, dict) and isinstance(event.get("timestamp"), int):
            ages[name] = max(0, current - event["timestamp"])
    return {"available": True, "qualified": True, "path": str(path), "state": payload, "ages": ages, "error": None}


def recovery_tree_counts(root: Path) -> dict:
    root = root.resolve()
    parent = root.parent
    rollback = sum(1 for path in parent.glob(f".{root.name}.rollback-*") if path.is_dir())
    failed = sum(1 for path in parent.glob(f".{root.name}.failed-*") if path.is_dir())
    return {"rollback": rollback, "failed": failed, "total": rollback + failed}
