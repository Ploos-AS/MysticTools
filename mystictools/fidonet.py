from __future__ import annotations

from pathlib import Path

from .fidonet_config import fidonet_config

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


def _scan_files(directory: Path, *, max_depth: int = 2) -> tuple[list[Path], list[str]]:
    if not directory.is_dir():
        return [], []
    results: list[Path] = []
    errors: list[str] = []
    stack: list[tuple[Path, int]] = [(directory, 0)]
    while stack:
        current, depth = stack.pop()
        try:
            entries = list(current.iterdir())
        except OSError as exc:
            errors.append(f"unable to scan {current}: {exc}")
            continue
        for entry in entries:
            try:
                if entry.is_file():
                    results.append(entry)
                elif entry.is_dir() and depth < max_depth:
                    stack.append((entry, depth + 1))
            except OSError as exc:
                errors.append(f"unable to inspect {entry}: {exc}")
    return results, errors


def _poll_context(processes: dict | None) -> dict:
    active = []
    for process in (processes or {}).get("mis", []):
        argv = process.get("argv") or []
        if len(argv) >= 2 and argv[1].lower() == "poll":
            active.append({
                "pid": process.get("pid"),
                "argv": argv,
                "exe": process.get("exe"),
            })
    return {
        "source": "procfs" if processes is not None else None,
        "active": bool(active),
        "processes": active,
        "count": len(active),
    }


def fidonet_snapshot(root: Path, processes: dict | None = None) -> dict:
    config = fidonet_config(root)
    inbound = Path(config["paths"]["inbound"]["path"])
    inbound_unsecured = Path(config["paths"]["inbound_unsecured"]["path"])
    outbound_primary = Path(config["paths"]["outbound_primary"]["path"])
    semaphore = Path(config["paths"]["semaphore"]["path"])
    outbound_root = outbound_primary.parent
    echomail_root = inbound.parent

    candidates = {
        "echomail_root": echomail_root,
        "inbound": inbound,
        "inbound_unsecured": inbound_unsecured,
        "outbound_primary": outbound_primary,
        "outbound_root": outbound_root,
        "semaphore": semaphore,
    }
    paths = {}
    scan_errors: list[str] = []
    for name, path in candidates.items():
        try:
            exists = path.exists()
            is_dir = path.is_dir()
        except OSError as exc:
            exists = False
            is_dir = False
            scan_errors.append(f"unable to inspect {path}: {exc}")
        paths[name] = {
            "path": str(path),
            "exists": exists,
            "is_dir": is_dir,
            "qualified": config["paths"].get(name, {}).get("qualified") if name in config["paths"] else None,
            "source": config["paths"].get(name, {}).get("source") if name in config["paths"] else "derived",
        }

    semaphores = []
    try:
        semaphore_is_dir = semaphore.is_dir()
    except OSError as exc:
        semaphore_is_dir = False
        scan_errors.append(f"unable to inspect {semaphore}: {exc}")
    if semaphore_is_dir:
        for name in _SEMAPHORE_NAMES:
            path = semaphore / name
            try:
                exists = path.exists()
            except OSError as exc:
                scan_errors.append(f"unable to inspect {path}: {exc}")
                continue
            if exists:
                record = {"name": name, **_file_record(path)}
                semaphores.append(record)
                if not record["available"] and record["error"]:
                    scan_errors.append(f"unable to stat {path}: {record['error']}")

    outbound_files, outbound_errors = _scan_files(outbound_root, max_depth=2)
    scan_errors.extend(outbound_errors)
    busy = [_file_record(path) for path in outbound_files if path.suffix.lower() in _BUSY_SUFFIXES]
    queue = [_file_record(path) for path in outbound_files if path.suffix.lower() in _PACKET_SUFFIXES]

    inbound_files, inbound_errors = _scan_files(inbound, max_depth=1)
    scan_errors.extend(inbound_errors)
    inbound_packets = [_file_record(path) for path in inbound_files if path.suffix.lower() in {".pkt", ".tic"}]

    for record in [*busy, *queue, *inbound_packets]:
        if not record["available"] and record["error"]:
            scan_errors.append(f"unable to stat {record['path']}: {record['error']}")

    signals = {
        "echomail_in": any(item["name"] == "echomail.in" for item in semaphores),
        "echomail_out": any(item["name"] == "echomail.out" for item in semaphores),
        "netmail_out": any(item["name"] == "netmail.out" for item in semaphores),
        "busy_count": len(busy),
        "queued_outbound_count": len(queue),
        "inbound_packet_count": len(inbound_packets),
    }

    if config.get("config_error"):
        scan_errors.insert(0, config["config_error"])

    return {
        "source": config["provider"],
        "qualified_config": config["qualified_config"],
        "qualified_scan": not scan_errors,
        "config": config,
        "paths": paths,
        "semaphores": semaphores,
        "busy_files": busy,
        "outbound_files": queue,
        "inbound_packets": inbound_packets,
        "signals": signals,
        "poll": _poll_context(processes),
        "scan_errors": scan_errors,
    }
