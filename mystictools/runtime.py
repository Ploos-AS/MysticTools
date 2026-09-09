from __future__ import annotations

import os
import re
from pathlib import Path

_NODE_RE = re.compile(r"^-N(\d+)$", re.IGNORECASE)
_VERSION_RE = re.compile(r"Mystic(?:\s+BBS)?[^\n\r]{0,80}?([0-9]+\.[0-9]+)\s+(?:Alpha\s+)?([A-Z]?\d+)", re.IGNORECASE)


def _read_cmdline(path: Path) -> list[str]:
    try:
        raw = path.read_bytes()
    except (OSError, PermissionError):
        return []
    return [part.decode("utf-8", errors="replace") for part in raw.split(b"\0") if part]


def _read_exe(path: Path) -> str | None:
    try:
        return os.readlink(path)
    except (OSError, PermissionError):
        return None


def parse_node_number(argv: list[str]) -> int | None:
    for arg in argv[1:]:
        match = _NODE_RE.match(arg)
        if match:
            return int(match.group(1))
    return None


def discover_processes(proc_root: Path = Path("/proc")) -> dict:
    mis = []
    nodes = []
    if not proc_root.is_dir():
        return {"source": "procfs", "available": False, "mis": [], "nodes": []}

    for entry in proc_root.iterdir():
        if not entry.name.isdigit() or not entry.is_dir():
            continue
        argv = _read_cmdline(entry / "cmdline")
        exe = _read_exe(entry / "exe")
        if not argv and not exe:
            continue

        command = Path(argv[0]).name.lower() if argv else ""
        exe_name = Path(exe).name.lower() if exe else ""
        record = {
            "pid": int(entry.name),
            "argv": argv,
            "exe": exe,
        }
        if command == "mis" or exe_name == "mis":
            mis.append(record)
        elif command == "mystic" or exe_name == "mystic":
            record["node"] = parse_node_number(argv)
            record["node_source"] = "argv" if record["node"] is not None else None
            nodes.append(record)

    mis.sort(key=lambda item: item["pid"])
    nodes.sort(key=lambda item: item["pid"])
    return {
        "source": "procfs",
        "available": True,
        "mis": mis,
        "nodes": nodes,
    }


def detect_version(root: Path) -> dict:
    candidates = (
        root / "whatsnew.txt",
        root / "WHATSNEW.TXT",
        root / "docs" / "whatsnew.txt",
        root / "docs" / "WHATSNEW.TXT",
    )
    for path in candidates:
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        match = _VERSION_RE.search(text)
        if match:
            return {
                "version": match.group(1),
                "build": match.group(2).upper(),
                "source": str(path),
            }
    return {"version": None, "build": None, "source": None}


def runtime_snapshot(root: Path, proc_root: Path = Path("/proc")) -> dict:
    processes = discover_processes(proc_root)
    return {
        "version": detect_version(root),
        "processes": processes,
        "mis_running": bool(processes["mis"]),
        "active_process_count": len(processes["nodes"]),
    }
