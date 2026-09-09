from __future__ import annotations

import re
from pathlib import Path

_TEMP_RE = re.compile(r"^temp(\d+)$", re.IGNORECASE)
_DROPFILES = {
    "DOOR.SYS": "door-sys",
    "CHAIN.TXT": "chain-txt",
    "DORINFO1.DEF": "dorinfo1-def",
    "door32.sys": "door32-sys",
}


def _record(path: Path) -> dict:
    try:
        stat = path.stat()
    except OSError as exc:
        return {
            "path": str(path),
            "available": False,
            "size": None,
            "mtime": None,
            "readable": False,
            "error": str(exc),
        }
    readable = False
    error = None
    try:
        with path.open("rb") as handle:
            handle.read(1)
        readable = True
    except OSError as exc:
        error = str(exc)
    return {
        "path": str(path),
        "available": True,
        "size": stat.st_size,
        "mtime": stat.st_mtime,
        "readable": readable,
        "error": error,
    }


def discover_node_temp_dirs(root: Path) -> tuple[list[dict], list[str]]:
    errors: list[str] = []
    try:
        entries = list(root.iterdir())
    except OSError as exc:
        return [], [f"unable to scan {root}: {exc}"]

    found = []
    for entry in entries:
        try:
            is_dir = entry.is_dir()
        except OSError as exc:
            errors.append(f"unable to inspect {entry}: {exc}")
            continue
        if not is_dir:
            continue
        match = _TEMP_RE.match(entry.name)
        if not match:
            continue
        found.append({"node": int(match.group(1)), "path": str(entry)})
    found.sort(key=lambda item: item["node"])
    return found, errors


def _dropfiles_for(directory: Path) -> tuple[list[dict], list[str]]:
    found = []
    errors: list[str] = []
    try:
        entries = list(directory.iterdir())
    except OSError as exc:
        return found, [f"unable to scan {directory}: {exc}"]

    for entry in entries:
        try:
            is_file = entry.is_file()
        except OSError as exc:
            errors.append(f"unable to inspect {entry}: {exc}")
            continue
        if not is_file:
            continue
        kind = _DROPFILES.get(entry.name)
        if kind is None:
            continue
        record = {"name": entry.name, "kind": kind, **_record(entry)}
        found.append(record)
        if record.get("error"):
            errors.append(f"unable to read {entry}: {record['error']}")
    found.sort(key=lambda item: item["name"].lower())
    return found, errors


def doors_snapshot(root: Path) -> dict:
    node_dirs, scan_errors = discover_node_temp_dirs(root)
    nodes = []
    total_dropfiles = 0
    unreadable = 0

    for item in node_dirs:
        directory = Path(item["path"])
        dropfiles, errors = _dropfiles_for(directory)
        scan_errors.extend(errors)
        total_dropfiles += len(dropfiles)
        unreadable += sum(1 for entry in dropfiles if not entry["readable"])
        nodes.append(
            {
                "node": item["node"],
                "path": item["path"],
                "dropfiles": dropfiles,
                "dropfile_count": len(dropfiles),
                "formats": sorted({entry["kind"] for entry in dropfiles}),
            }
        )

    return {
        "source": "filesystem-node-temp",
        "qualified": not scan_errors,
        "read_only": True,
        "nodes": nodes,
        "node_temp_count": len(nodes),
        "dropfile_count": total_dropfiles,
        "unreadable_dropfile_count": unreadable,
        "scan_errors": scan_errors,
        "supported_formats": sorted(set(_DROPFILES.values())),
        "notes": [
            "Mystic creates door drop files in per-node tempN directories.",
            "MysticTools reports metadata only and does not parse user/session contents in M2.3.",
        ],
    }
