from __future__ import annotations

from pathlib import Path

from .doors import doors_snapshot
from .fidonet import fidonet_snapshot
from .network import network_snapshot
from .runtime import runtime_snapshot
from .users import users_snapshot

SCHEMA_VERSION = 1


def _sum_numeric(records: list[dict], field: str) -> int | None:
    values = [item.get(field) for item in records]
    numeric = [value for value in values if isinstance(value, int) and not isinstance(value, bool) and value >= 0]
    if not numeric:
        return None
    return sum(numeric)


def stats_snapshot(root: Path) -> dict:
    users = users_snapshot(root)
    runtime = runtime_snapshot(root)
    processes = runtime["processes"]
    network = network_snapshot(processes)
    fidonet = fidonet_snapshot(root, processes=processes)
    doors = doors_snapshot(root)

    user_records = users["users"] if users["qualified"] else []
    user_totals = {
        "users": users["count"] if users["qualified"] else None,
        "calls": _sum_numeric(user_records, "calls") if users["qualified"] else None,
        "uploads": _sum_numeric(user_records, "uploads") if users["qualified"] else None,
        "downloads": _sum_numeric(user_records, "downloads") if users["qualified"] else None,
        "posts": _sum_numeric(user_records, "posts") if users["qualified"] else None,
    }

    runtime_available = bool(processes["available"])
    return {
        "schema_version": SCHEMA_VERSION,
        "root": str(root),
        "sources": {
            "users_qualified": users["qualified"],
            "runtime_available": runtime_available,
            "network_available": network["available"],
            "fidonet_config_qualified": fidonet["qualified_config"],
        },
        "users": user_totals,
        "runtime": {
            "mis_running": runtime["mis_running"] if runtime_available else None,
            "node_processes": runtime["active_process_count"] if runtime_available else None,
            "listeners": len(network["listeners"]) if network["available"] else None,
        },
        "fidonet": {
            "busy_files": fidonet["signals"]["busy_count"],
            "outbound_queue_candidates": fidonet["signals"]["queued_outbound_count"],
            "inbound_packets": fidonet["signals"]["inbound_packet_count"],
            "poll_active": fidonet["poll"]["active"] if runtime_available else None,
        },
        "doors": {
            "node_temp_dirs": doors["node_temp_count"],
            "dropfiles": doors["dropfile_count"],
            "unreadable_dropfiles": doors["unreadable_dropfile_count"],
        },
    }
