from __future__ import annotations

from pathlib import Path

from .diagnostics import discover_logs

DEFAULT_TAIL = 50
MAX_TAIL = 5000


def _safe_tail_count(value: int) -> int:
    if value < 0:
        raise ValueError("tail must be >= 0")
    return min(value, MAX_TAIL)


def select_logs(root: Path, name: str | None = None) -> list[Path]:
    discovered = [Path(item) for item in discover_logs(root)["files"]]
    if name is None:
        return discovered

    needle = name.casefold()
    matches = [
        path
        for path in discovered
        if path.name.casefold() == needle or path.stem.casefold() == needle
    ]
    if matches:
        return matches

    return [path for path in discovered if needle in path.name.casefold()]


def read_log(path: Path, tail: int = DEFAULT_TAIL, contains: str | None = None) -> dict:
    tail = _safe_tail_count(tail)
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return {
            "path": str(path),
            "available": False,
            "error": str(exc),
            "lines": [],
            "matched": 0,
        }

    lines = text.splitlines()
    if contains is not None:
        needle = contains.casefold()
        lines = [line for line in lines if needle in line.casefold()]
    if tail:
        lines = lines[-tail:]
    else:
        lines = []

    return {
        "path": str(path),
        "available": True,
        "error": None,
        "lines": lines,
        "matched": len(lines),
    }


def log_snapshot(
    root: Path,
    *,
    name: str | None = None,
    tail: int = DEFAULT_TAIL,
    contains: str | None = None,
) -> dict:
    selected = select_logs(root, name)
    entries = [read_log(path, tail=tail, contains=contains) for path in selected]
    unavailable = sum(1 for entry in entries if not entry["available"])
    return {
        "source": "filesystem",
        "root": str(root),
        "selector": name,
        "contains": contains,
        "tail": _safe_tail_count(tail),
        "files": entries,
        "file_count": len(entries),
        "unavailable_count": unavailable,
        "ok": unavailable == 0,
    }
