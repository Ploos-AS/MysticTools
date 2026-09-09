from __future__ import annotations

import ipaddress
import os
import re
from pathlib import Path

_SOCKET_RE = re.compile(r"^socket:\[(\d+)\]$")
_LISTEN_STATE = "0A"


def _decode_ipv4(hex_address: str) -> str:
    raw = bytes.fromhex(hex_address)
    return str(ipaddress.IPv4Address(raw[::-1]))


def _decode_ipv6(hex_address: str) -> str:
    raw = bytes.fromhex(hex_address)
    words = [raw[i : i + 4][::-1] for i in range(0, 16, 4)]
    return str(ipaddress.IPv6Address(b"".join(words)))


def _parse_table(path: Path, family: str) -> list[dict]:
    if not path.is_file():
        return []
    try:
        lines = path.read_text(encoding="ascii", errors="replace").splitlines()
    except OSError:
        return []

    rows = []
    for line in lines[1:]:
        parts = line.split()
        if len(parts) < 10 or parts[3] != _LISTEN_STATE:
            continue
        local_hex, port_hex = parts[1].split(":", 1)
        inode = parts[9]
        try:
            address = _decode_ipv4(local_hex) if family == "tcp" else _decode_ipv6(local_hex)
            port = int(port_hex, 16)
        except (ValueError, ipaddress.AddressValueError):
            continue
        rows.append({"family": family, "address": address, "port": port, "inode": inode})
    return rows


def _socket_inodes_for_pid(proc_root: Path, pid: int) -> set[str]:
    fd_dir = proc_root / str(pid) / "fd"
    try:
        entries = list(fd_dir.iterdir())
    except OSError:
        return set()
    inodes = set()
    for entry in entries:
        try:
            target = os.readlink(entry)
        except OSError:
            continue
        match = _SOCKET_RE.match(target)
        if match:
            inodes.add(match.group(1))
    return inodes


def network_snapshot(processes: dict, proc_root: Path = Path("/proc")) -> dict:
    net_root = proc_root / "net"
    listeners = _parse_table(net_root / "tcp", "tcp") + _parse_table(net_root / "tcp6", "tcp6")
    if not net_root.is_dir():
        return {"available": False, "source": "procfs", "listeners": [], "processes": []}

    tracked = []
    for kind, records in (("mis", processes.get("mis", [])), ("mystic", processes.get("nodes", []))):
        for process in records:
            pid = int(process["pid"])
            inodes = _socket_inodes_for_pid(proc_root, pid)
            owned = [dict(item) for item in listeners if item["inode"] in inodes]
            for item in owned:
                item.pop("inode", None)
            tracked.append({"kind": kind, "pid": pid, "listeners": owned})

    flattened = []
    for item in tracked:
        for listener in item["listeners"]:
            flattened.append({"kind": item["kind"], "pid": item["pid"], **listener})
    flattened.sort(key=lambda item: (item["port"], item["family"], item["pid"]))

    return {
        "available": True,
        "source": "procfs",
        "listeners": flattened,
        "processes": tracked,
    }


def health_snapshot(runtime: dict, network: dict) -> dict:
    checks = [
        {
            "name": "procfs",
            "status": "ok" if runtime["processes"]["available"] else "unknown",
            "detail": "runtime procfs available" if runtime["processes"]["available"] else "runtime procfs unavailable",
        },
        {
            "name": "mis",
            "status": "ok" if runtime["mis_running"] else "warning",
            "detail": "MIS process detected" if runtime["mis_running"] else "MIS process not detected",
        },
        {
            "name": "network",
            "status": "ok" if network["available"] else "unknown",
            "detail": f"{len(network['listeners'])} tracked listener(s)" if network["available"] else "network procfs unavailable",
        },
    ]
    severity_order = {"ok": 0, "warning": 1, "unknown": 2, "critical": 3}
    worst = max(checks, key=lambda item: severity_order[item["status"]])["status"]
    return {"status": worst, "checks": checks, "listener_count": len(network["listeners"])}
