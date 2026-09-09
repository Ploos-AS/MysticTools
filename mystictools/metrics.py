from __future__ import annotations

from pathlib import Path

from .diagnostics import operational_checks
from .network import health_snapshot, network_snapshot
from .runtime import runtime_snapshot

SCHEMA_VERSION = 1


def metrics_snapshot(root: Path) -> dict:
    runtime = runtime_snapshot(root)
    network = network_snapshot(runtime["processes"])
    operations = operational_checks(root)
    health = health_snapshot(runtime, network)

    values = {
        "mystictools_up": 1 if runtime["processes"]["available"] else 0,
        "mystic_mis_running": 1 if runtime["mis_running"] else 0,
        "mystic_node_processes": runtime["active_process_count"],
        "mystic_listeners": len(network["listeners"]) if network["available"] else 0,
        "mystic_logs_discovered": operations["logs"]["count"],
        "mystic_disk_free_bytes": operations["disk"]["free_bytes"] if operations["disk"]["available"] else None,
        "mystic_disk_free_percent": operations["disk"]["free_percent"] if operations["disk"]["available"] else None,
        "mystic_operational_warnings": operations["warning_count"],
        "mystic_health_status": {"ok": 0, "warning": 1, "unknown": 2, "critical": 3}.get(health["status"], 2),
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "root": str(root),
        "health": health["status"],
        "values": values,
    }


def render_prometheus(snapshot: dict) -> str:
    help_text = {
        "mystictools_up": "Whether MysticTools procfs discovery is available.",
        "mystic_mis_running": "Whether a MIS process was detected.",
        "mystic_node_processes": "Number of detected Mystic node processes.",
        "mystic_listeners": "Number of listeners owned by detected MIS/Mystic processes.",
        "mystic_logs_discovered": "Number of candidate Mystic log files discovered.",
        "mystic_disk_free_bytes": "Free bytes on the filesystem containing the Mystic root.",
        "mystic_disk_free_percent": "Free filesystem percentage for the Mystic root.",
        "mystic_operational_warnings": "Number of current operational warnings.",
        "mystic_health_status": "Health status code: 0 ok, 1 warning, 2 unknown, 3 critical.",
    }
    lines: list[str] = []
    for name, value in snapshot["values"].items():
        if value is None:
            continue
        lines.append(f"# HELP {name} {help_text[name]}")
        lines.append(f"# TYPE {name} gauge")
        lines.append(f"{name} {value}")
    return "\n".join(lines) + "\n"
