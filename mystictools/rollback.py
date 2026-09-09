from __future__ import annotations

import os
import tempfile
from pathlib import Path

from .restore_transaction import clear_journal, recovery_status
from .runtime import runtime_snapshot


def _runtime_guard(root: Path) -> tuple[bool, bool | None, list[str]]:
    runtime = runtime_snapshot(root)
    processes = runtime["processes"]
    available = bool(processes.get("available"))
    running = bool(processes.get("mis") or processes.get("nodes")) if available else None
    errors: list[str] = []
    if not available:
        errors.append("runtime state is unavailable; rollback requires verified stopped Mystic/MIS processes")
    elif running:
        errors.append("Mystic/MIS processes are running; stop the BBS before rollback")
    return available, running, errors


def rollback_preflight(root: Path, rollback_path: Path) -> dict:
    root = root.resolve()
    rollback_path = rollback_path.expanduser().resolve()
    runtime_available, bbs_running, errors = _runtime_guard(root)
    warnings: list[str] = []

    expected_prefix = f".{root.name}.rollback-"
    if rollback_path.parent != root.parent:
        errors.append("rollback tree must be a sibling of the Mystic root")
    if not rollback_path.name.startswith(expected_prefix):
        errors.append(f"rollback tree name must start with {expected_prefix!r}")
    if not rollback_path.is_dir():
        errors.append("rollback tree does not exist or is not a directory")

    recovery = recovery_status(root)
    journal_matches = False
    if recovery.get("exists"):
        if not recovery.get("valid"):
            errors.append("restore transaction journal is invalid; inspect it manually before rollback")
        else:
            payload = recovery.get("payload") or {}
            recorded = payload.get("rollback")
            state = recovery.get("state")
            journal_matches = state in {"old-moved", "new-installed"} and recorded == str(rollback_path)
            if not journal_matches:
                errors.append("unfinished restore transaction blocks rollback of an unrelated recovery tree")
            else:
                warnings.append(f"rollback matches unfinished restore transaction state {state!r}")

    if not root.exists():
        warnings.append("current target root does not exist; rollback will install the saved tree directly")

    return {
        "ok": not errors,
        "root": str(root),
        "rollback_path": str(rollback_path),
        "runtime_available": runtime_available,
        "bbs_running": bbs_running,
        "restore_transaction": recovery,
        "journal_matches_rollback": journal_matches,
        "errors": errors,
        "warnings": warnings,
        "mode": "rollback-preflight-only",
    }


def execute_rollback(root: Path, rollback_path: Path) -> dict:
    preflight = rollback_preflight(root, rollback_path)
    if not preflight["ok"]:
        return {
            **preflight,
            "rolled_back": False,
            "failed_tree_path": None,
            "transaction_journal_cleared": False,
            "mode": "guarded-rollback",
        }

    root = Path(preflight["root"])
    rollback_path = Path(preflight["rollback_path"])
    failed_tree: Path | None = None
    journal_cleared = False

    try:
        runtime_available, bbs_running, runtime_errors = _runtime_guard(root)
        if not runtime_available or bbs_running:
            raise OSError("; ".join(runtime_errors) or "runtime state changed before rollback commit")

        if root.exists():
            failed_tree = Path(tempfile.mkdtemp(prefix=f".{root.name}.failed-", dir=root.parent))
            failed_tree.rmdir()
            os.replace(root, failed_tree)
        try:
            os.replace(rollback_path, root)
        except OSError:
            if failed_tree is not None and failed_tree.exists() and not root.exists():
                os.replace(failed_tree, root)
                failed_tree = None
            raise

        if preflight.get("journal_matches_rollback"):
            clear_journal(root)
            journal_cleared = True

        return {
            **preflight,
            "ok": True,
            "rolled_back": True,
            "failed_tree_path": str(failed_tree) if failed_tree is not None else None,
            "transaction_journal_cleared": journal_cleared,
            "mode": "guarded-rollback",
        }
    except OSError as exc:
        return {
            **preflight,
            "ok": False,
            "rolled_back": False,
            "failed_tree_path": str(failed_tree) if failed_tree is not None and failed_tree.exists() else None,
            "transaction_journal_cleared": False,
            "mode": "guarded-rollback",
            "errors": preflight["errors"] + [str(exc)],
        }


def discover_recovery_trees(root: Path) -> dict:
    root = root.resolve()
    parent = root.parent
    rollback_prefix = f".{root.name}.rollback-"
    failed_prefix = f".{root.name}.failed-"
    rollback = sorted(str(path) for path in parent.glob(f"{rollback_prefix}*") if path.is_dir())
    failed = sorted(str(path) for path in parent.glob(f"{failed_prefix}*") if path.is_dir())
    recovery = recovery_status(root)
    return {
        "root": str(root),
        "rollback_trees": rollback,
        "failed_trees": failed,
        "restore_transaction": recovery,
        "restore_transaction_journal": recovery.get("path") if recovery.get("exists") else None,
        "cleanup_policy": "manual-only",
    }
