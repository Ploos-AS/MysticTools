from __future__ import annotations

from pathlib import Path

_SEMAPHORE_NAMES = ("echomail.in", "echomail.out", "netmail.out")
_BUSY_SUFFIXES = {".bsy", ".csy"}
_PACKET_SUFFIXES = {".pkt", ".flo", ".clo", ".dlo", ".hlo"}


def _file_record(path: Path) -> dict:
    try:
        stat = path.stat()
    except OSError as exc:
        return {"path": str(path), "available": False, "size": None, "mtime": None, "error": str(exc)}
    return {
        "path": str(path),
        "available": True,
        "size": stat.st_size,
        "mtime": stat.st_mtime,
        "error": None,
    }


def _scan_files(directory: Path, *, max_depth: int = 2) -> list[Path]:
    if not directory.is_dir():
        return []
    results: list[Path] = []
    stack: list[tuple[Path, int]] = [(directory, 0)]
    while stack:
        current, depth = stack.pop()
        try:
            entries = list(current.iterdir())
        except OSError:
            continue
        for entry in entries:
            if entry.is_file():
                results.append(entry)
            elif entry.is_dir() and depth < max_depth:
                stack.append((entry, depth + 1))
    return results


def fidonet_snapshot(root: Path) -> dict:
    echomail = root / "echomail"
    semaphore = root / "semaphore"
    candidates = {
        "echomail_root": echomail,
        "inbound": echomail / "in",
        "inbound_unsecured": echomail / "in" / "unsecure",
        "outbound_primary": echomail / "out" / "primary",
        "outbound_root": echomail / "out",
        "semaphore": semaphore,
    }
    paths = {name: {"path": str(path), "exists": path.exists(), "is_dir": path.is_dir()} for name, path in candidates.items()}

    semaphores = []
    if semaphore.is_dir():
        for name in _SEMAPHORE_NAMES:
            path = semaphore / name
            if path.exists():
                semaphores.append({"name": name, **_file_record(path)})

    outbound_files = _scan_files(candidates["outbound_root"], max_depth=2)
    busy = [_file_record(path) for path in outbound_files if path.suffix.lower() in _BUSY_SUFFIXES]
    queue = [_file_record(path) for path in outbound_files if path.suffix.lower() in _PACKET_SUFFIXES]

    inbound_files = _scan_files(candidates["inbound"], max_depth=1)
    inbound_packets = [_file_record(path) for path in inbound_files if path.suffix.lower() in {".pkt", ".tic"}]

    signals = {
        "echomail_in": any(item["name"] == "echomail.in" for item in semaphores),
        "echomail_out": any(item["name"] == "echomail.out" for item in semaphores),
        "netmail_out": any(item["name"] == "netmail.out" for item in semaphores),
        "busy_count": len(busy),
        "queued_outbound_count": len(queue),
        "inbound_packet_count": len(inbound_packets),
    }

    return {
        "source": "filesystem-defaults",
        "qualified_config": False,
        "paths": paths,
        "semaphores": semaphores,
        "busy_files": busy,
        "outbound_files": queue,
        "inbound_packets": inbound_packets,
        "signals": signals,
    }
