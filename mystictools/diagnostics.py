from __future__ import annotations

import os
import shutil
from pathlib import Path

EXIT_OK = 0
EXIT_WARNING = 1
EXIT_NOT_FOUND = 2
EXIT_UNAVAILABLE = 3

MIN_FREE_BYTES = 512 * 1024 * 1024


def _identity(path: Path) -> dict:
    try:
        stat = path.stat()
    except OSError as exc:
        return {"available": False, "error": str(exc), "uid": None, "gid": None}
    return {
        "available": True,
        "error": None,
        "uid": stat.st_uid,
        "gid": stat.st_gid,
    }


def permission_snapshot(root: Path) -> dict:
    paths = {
        "root": root,
        "mis": root / "mis",
        "mutil": root / "mutil",
        "cfg": root / "cfg",
        "data": root / "data",
        "logs": root / "logs",
    }
    items = {}
    for name, path in paths.items():
        exists = path.exists()
        items[name] = {
            "path": str(path),
            "exists": exists,
            "readable": exists and os.access(path, os.R_OK),
            "searchable": exists and path.is_dir() and os.access(path, os.X_OK),
            "executable": exists and path.is_file() and os.access(path, os.X_OK),
            "identity": _identity(path) if exists else None,
        }

    root_identity = items["root"]["identity"] or {}
    root_owner = (root_identity.get("uid"), root_identity.get("gid"))
    ownership_mismatches = []
    if root_identity.get("available"):
        for name, item in items.items():
            identity = item.get("identity") or {}
            if name == "root" or not identity.get("available"):
                continue
            owner = (identity.get("uid"), identity.get("gid"))
            if owner != root_owner:
                ownership_mismatches.append(
                    {
                        "name": name,
                        "path": item["path"],
                        "uid": owner[0],
                        "gid": owner[1],
                    }
                )

    return {
        "items": items,
        "root_owner": {"uid": root_owner[0], "gid": root_owner[1]},
        "ownership_mismatches": ownership_mismatches,
    }


def disk_snapshot(root: Path) -> dict:
    try:
        usage = shutil.disk_usage(root)
    except OSError as exc:
        return {
            "available": False,
            "error": str(exc),
            "total_bytes": None,
            "used_bytes": None,
            "free_bytes": None,
            "free_percent": None,
            "low_space": None,
        }
    free_percent = (usage.free / usage.total * 100.0) if usage.total else 0.0
    return {
        "available": True,
        "error": None,
        "total_bytes": usage.total,
        "used_bytes": usage.used,
        "free_bytes": usage.free,
        "free_percent": round(free_percent, 2),
        "low_space": usage.free < MIN_FREE_BYTES,
    }


def discover_logs(root: Path) -> dict:
    directories = []
    files = []
    candidates = (root / "logs", root / "log")
    for directory in candidates:
        if not directory.is_dir():
            continue
        directories.append(str(directory))
        try:
            entries = sorted(directory.iterdir(), key=lambda p: p.name.lower())
        except OSError:
            continue
        for entry in entries:
            if entry.is_file() and entry.suffix.lower() in {".log", ".txt"}:
                files.append(str(entry))

    try:
        root_entries = sorted(root.iterdir(), key=lambda p: p.name.lower())
    except OSError:
        root_entries = []
    for entry in root_entries:
        if entry.is_file() and entry.suffix.lower() == ".log":
            files.append(str(entry))

    return {
        "directories": directories,
        "files": sorted(set(files)),
        "count": len(set(files)),
    }


def operational_checks(root: Path) -> dict:
    permissions = permission_snapshot(root)
    disk = disk_snapshot(root)
    logs = discover_logs(root)
    checks = []

    for name, item in permissions["items"].items():
        if not item["exists"]:
            continue
        if not item["readable"]:
            checks.append({"name": f"permission:{name}:read", "status": "warning", "detail": item["path"]})
        if Path(item["path"]).is_dir() and not item["searchable"]:
            checks.append({"name": f"permission:{name}:search", "status": "warning", "detail": item["path"]})
        if name in {"mis", "mutil"} and Path(item["path"]).is_file() and not item["executable"]:
            checks.append({"name": f"permission:{name}:execute", "status": "warning", "detail": item["path"]})

    if permissions["ownership_mismatches"]:
        checks.append({
            "name": "ownership:mixed",
            "status": "warning",
            "detail": f"{len(permissions['ownership_mismatches'])} standard path(s) differ from root uid/gid",
        })

    if not disk["available"]:
        checks.append({"name": "disk:usage", "status": "warning", "detail": disk["error"] or "unavailable"})
    elif disk["low_space"]:
        checks.append({
            "name": "disk:free",
            "status": "warning",
            "detail": f"{disk['free_bytes']} bytes free; threshold is {MIN_FREE_BYTES}",
        })

    checks.append({
        "name": "logs:discovery",
        "status": "ok" if logs["directories"] else "warning",
        "detail": f"{logs['count']} candidate log file(s) in {len(logs['directories'])} log dir(s)",
    })

    warning_count = sum(1 for item in checks if item["status"] == "warning")
    return {
        "permissions": permissions,
        "disk": disk,
        "logs": logs,
        "checks": checks,
        "warning_count": warning_count,
        "ok": warning_count == 0,
    }
