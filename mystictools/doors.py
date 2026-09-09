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
    try:
        with path.open("rb") as handle:
            handle.read(1)
        readable = True
    except OSError:
        pass
    return {
        "path": str(path),
        "available": True,
        "size": stat.st_size,
        "mtime": stat.st_mtime,
        "readable": readable,
        "error": None,
    }


def discover_node_temp_dirs(root: Path) -> list[dict]:
    try:
        entries = list(root.iterdir())
    except OSError:
        return []

    found = []
    for entry in entries:
        if not entry.is_dir():
            continue
        match = _TEMP_RE.match(entry.name)
        if not match:
            continue
        found.append({"node": int(match.group(1)), "path": str(entry)})
    found.sort(key=lambda item: item["node"])
    return found


def _dropfiles_for(directory: Path) -> list[dict]:
    found = []
    try:
        entries = list(directory.iterdir())
    except OSError:
        return found

    for entry in entries:
        if not entry.is_file():
            continue
        kind = _DROPFILES.get(entry.name)
        if kind is None:
            continue
        found.append({"name": entry.name, "kind": kind, **_record(entry)})
    found.sort(key=lambda item: item["name"].lower())
    return found


def doors_snapshot(root: Path) -> dict:
    node_dirs = discover_node_temp_dirs(root)
    nodes = []
    total_dropfiles = 0
    unreadable = 0

    for item in node_dirs:
        directory = Path(item["path"])
        dropfiles = _dropfiles_for(directory)
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
        "qualified": True,
        "read_only": True,
        "nodes": nodes,
        "node_temp_count": len(nodes),
        "dropfile_count": total_dropfiles,
        "unreadable_dropfile_count": unreadable,
        "supported_formats": sorted(set(_DROPFILES.values())),
        "notes": [
            "Mystic creates door drop files in per-node tempN directories.",
            "MysticTools reports metadata only and does not parse user/session contents in M2.3.",
        ],
    }
