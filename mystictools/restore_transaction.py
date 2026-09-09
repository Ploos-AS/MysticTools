from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path

JOURNAL_SCHEMA_VERSION = 1
VALID_STATES = {"prepared", "old-moved", "new-installed"}


def journal_path(root: Path) -> Path:
    root = root.resolve()
    return root.parent / f".{root.name}.restore-transaction.json"


def _safe_optional_sibling(root: Path, value: object, prefix: str) -> tuple[str | None, str | None]:
    if value is None:
        return None, None
    if not isinstance(value, str) or not value:
        return None, "path is not a non-empty string"
    candidate = Path(value).expanduser()
    try:
        resolved_parent = candidate.parent.resolve()
    except OSError:
        return None, "path parent cannot be resolved"
    if resolved_parent != root.parent.resolve():
        return None, "path is not a sibling of the Mystic root"
    if not candidate.name.startswith(prefix):
        return None, f"path name does not start with {prefix!r}"
    return str(candidate), None


def write_journal(root: Path, *, state: str, archive: Path, archive_sha256: str, stage: Path | None, rollback: Path | None) -> Path:
    root = root.resolve()
    if state not in VALID_STATES:
        raise ValueError(f"unsupported restore transaction state: {state}")
    path = journal_path(root)
    payload = {
        "schema_version": JOURNAL_SCHEMA_VERSION,
        "updated_at": int(time.time()),
        "state": state,
        "root": str(root),
        "archive": str(archive),
        "archive_sha256": archive_sha256,
        "stage": str(stage) if stage is not None else None,
        "rollback": str(rollback) if rollback is not None else None,
    }
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temp = Path(temp_name)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
        os.chmod(path, 0o600)
        return path
    except Exception:
        try:
            os.close(fd)
        except OSError:
            pass
        temp.unlink(missing_ok=True)
        raise


def read_journal(root: Path) -> dict:
    root = root.resolve()
    path = journal_path(root)
    if not path.exists():
        return {"exists": False, "valid": False, "path": str(path), "state": None, "payload": None, "errors": []}

    errors: list[str] = []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return {"exists": True, "valid": False, "path": str(path), "state": None, "payload": None, "errors": [f"unable to read restore transaction journal: {exc}"]}

    if not isinstance(payload, dict):
        return {"exists": True, "valid": False, "path": str(path), "state": None, "payload": None, "errors": ["restore transaction journal is not an object"]}

    if payload.get("schema_version") != JOURNAL_SCHEMA_VERSION:
        errors.append("unsupported restore transaction journal schema")
    state = payload.get("state")
    if state not in VALID_STATES:
        errors.append("restore transaction journal has invalid state")
    if payload.get("root") != str(root):
        errors.append("restore transaction journal root does not match selected Mystic root")
    archive = payload.get("archive")
    if not isinstance(archive, str) or not archive:
        errors.append("restore transaction journal archive is invalid")
    digest = payload.get("archive_sha256")
    if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdefABCDEF" for c in digest):
        errors.append("restore transaction journal archive SHA-256 is invalid")

    stage, stage_error = _safe_optional_sibling(root, payload.get("stage"), f".{root.name}.restore-")
    rollback, rollback_error = _safe_optional_sibling(root, payload.get("rollback"), f".{root.name}.rollback-")
    if stage_error:
        errors.append(f"invalid restore stage path: {stage_error}")
    if rollback_error:
        errors.append(f"invalid rollback path: {rollback_error}")

    normalized = dict(payload)
    normalized["stage"] = stage
    normalized["rollback"] = rollback
    if state == "prepared" and rollback is not None:
        errors.append("prepared transaction unexpectedly has a rollback path")
    if state == "old-moved" and rollback is None:
        errors.append("old-moved transaction is missing rollback path")
    if state == "new-installed" and payload.get("stage") is not None:
        errors.append("new-installed transaction unexpectedly has a stage path")

    return {
        "exists": True,
        "valid": not errors,
        "path": str(path),
        "state": state if state in VALID_STATES else None,
        "payload": normalized,
        "errors": errors,
    }


def recovery_status(root: Path) -> dict:
    root = root.resolve()
    journal = read_journal(root)
    if not journal["exists"]:
        return {**journal, "classification": "none", "recommended_action": None}
    if not journal["valid"]:
        return {**journal, "classification": "invalid-journal", "recommended_action": "inspect-manually"}

    payload = journal["payload"] or {}
    state = journal["state"]
    stage = Path(payload["stage"]) if payload.get("stage") else None
    rollback = Path(payload["rollback"]) if payload.get("rollback") else None
    root_exists = root.exists()
    stage_exists = bool(stage and stage.exists())
    rollback_exists = bool(rollback and rollback.exists())

    if state == "prepared":
        classification = "staged-not-committed" if stage_exists else "prepared-stage-missing"
        action = "inspect-or-abort-staged-restore"
    elif state == "old-moved":
        if not root_exists and rollback_exists:
            classification = "old-root-moved-new-root-not-installed"
            action = "restore-recorded-rollback"
        else:
            classification = "old-moved-inconsistent"
            action = "inspect-manually"
    else:
        if root_exists:
            classification = "new-root-installed-journal-not-cleared"
            action = "verify-new-root-then-clear-or-rollback"
        else:
            classification = "new-installed-root-missing"
            action = "inspect-manually"

    return {
        **journal,
        "classification": classification,
        "recommended_action": action,
        "root_exists": root_exists,
        "stage_exists": stage_exists,
        "rollback_exists": rollback_exists,
    }


def clear_journal(root: Path) -> None:
    journal_path(root).unlink(missing_ok=True)
