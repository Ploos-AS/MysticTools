from __future__ import annotations

from pathlib import Path

from .diagnostics import operational_checks
from .doctor import doctor_snapshot
from .doors import doors_snapshot
from .fidonet import fidonet_snapshot
from .node_provider import load_node_snapshot
from .network import health_snapshot, network_snapshot
from .runtime import runtime_snapshot
from .users import users_snapshot

SCHEMA_VERSION = 2

_HEALTH_CODES = {"ok": 0, "warning": 1, "unknown": 2, "critical": 3}
_DOCTOR_CODES = {"ok": 0, "warning": 1, "critical": 2, "unavailable": 3}

_HELP_TEXT = {
    "mystictools_runtime_available": "Whether Linux procfs runtime discovery is available.",
    "mystictools_network_available": "Whether procfs network discovery is available.",
    "mystictools_mis_running": "Whether a MIS process was detected.",
    "mystictools_node_processes": "Number of detected Mystic node processes.",
    "mystictools_listener_count": "Number of listeners owned by detected MIS/Mystic processes.",
    "mystictools_logs_discovered": "Number of candidate Mystic log files discovered.",
    "mystictools_disk_free_bytes": "Free bytes on the filesystem containing the Mystic root.",
    "mystictools_disk_free_percent": "Free filesystem percentage for the Mystic root.",
    "mystictools_operational_warnings": "Number of current operational warnings.",
    "mystictools_health_status": "Health status code: 0 ok, 1 warning, 2 unknown, 3 critical.",
    "mystictools_doctor_status": "Doctor status code: 0 ok, 1 warning, 2 critical, 3 unavailable.",
    "mystictools_doctor_warnings": "Number of doctor findings with warning status.",
    "mystictools_doctor_critical": "Number of doctor findings with critical status.",
    "mystictools_doctor_unavailable": "Number of doctor findings with unavailable status.",
    "mystictools_node_provider_available": "Whether a Mystic native node provider exists and was readable.",
    "mystictools_node_provider_qualified": "Whether the native node provider passed qualification.",
    "mystictools_node_fragment_count": "Number of per-node Mystic snapshot fragment files discovered.",
    "mystictools_node_fragment_fresh": "Number of per-node snapshot fragments within the configured freshness window.",
    "mystictools_node_fragment_stale": "Number of per-node snapshot fragments outside the configured freshness window.",
    "mystictools_node_fragment_max_age_seconds": "Configured maximum accepted age for per-node snapshot fragments.",
    "mystictools_users_provider_available": "Whether a Mystic users snapshot exists and was readable.",
    "mystictools_users_provider_qualified": "Whether the Mystic users snapshot passed schema qualification.",
    "mystictools_users_count": "Number of privacy-safe Mystic user records in the qualified snapshot.",
    "mystictools_users_total_calls": "Sum of total calls across users in the qualified snapshot.",
    "mystictools_users_total_uploads": "Sum of uploaded files across users in the qualified snapshot.",
    "mystictools_users_total_downloads": "Sum of downloaded files across users in the qualified snapshot.",
    "mystictools_users_total_posts": "Sum of message posts across users in the qualified snapshot.",
    "mystictools_fidonet_config_qualified": "Whether all required FidoNet paths came from explicit qualified configuration.",
    "mystictools_fidonet_busy_files": "Number of detected FidoNet busy/control files.",
    "mystictools_fidonet_outbound_queue_candidates": "Number of detected outbound FidoNet queue/control candidates.",
    "mystictools_fidonet_inbound_packets": "Number of detected inbound packet/TIC candidates.",
    "mystictools_fidonet_poll_active": "Whether an active MIS POLL process was detected.",
    "mystictools_door_node_temp_dirs": "Number of detected Mystic node temp directories.",
    "mystictools_door_dropfiles": "Number of detected known Mystic door dropfiles.",
    "mystictools_door_unreadable_dropfiles": "Number of detected dropfiles that were not readable.",
}


def _sum_user_field(users: dict, field: str) -> int | None:
    if not users["qualified"]:
        return None
    values = [item.get(field) for item in users["users"]]
    numeric = [value for value in values if isinstance(value, int) and not isinstance(value, bool) and value >= 0]
    return sum(numeric) if numeric else None


def metrics_snapshot(root: Path) -> dict:
    runtime = runtime_snapshot(root)
    processes = runtime["processes"]
    runtime_available = bool(processes["available"])
    network = network_snapshot(processes)
    operations = operational_checks(root)
    health = health_snapshot(runtime, network)
    doctor = doctor_snapshot(root)
    provider = load_node_snapshot(root)
    users = users_snapshot(root)
    fidonet = fidonet_snapshot(root, processes=processes)
    doors = doors_snapshot(root)

    fragment_provider = str(provider.get("source", "")).startswith("fragment-")
    values = {
        "mystictools_runtime_available": 1 if runtime_available else 0,
        "mystictools_network_available": 1 if network["available"] else 0,
        "mystictools_mis_running": (1 if runtime["mis_running"] else 0) if runtime_available else None,
        "mystictools_node_processes": runtime["active_process_count"] if runtime_available else None,
        "mystictools_listener_count": len(network["listeners"]) if network["available"] else None,
        "mystictools_logs_discovered": operations["logs"]["count"],
        "mystictools_disk_free_bytes": operations["disk"]["free_bytes"] if operations["disk"]["available"] else None,
        "mystictools_disk_free_percent": operations["disk"]["free_percent"] if operations["disk"]["available"] else None,
        "mystictools_operational_warnings": operations["warning_count"],
        "mystictools_health_status": _HEALTH_CODES.get(health["status"], 2),
        "mystictools_doctor_status": _DOCTOR_CODES.get(doctor["status"], 3),
        "mystictools_doctor_warnings": doctor["counts"]["warning"],
        "mystictools_doctor_critical": doctor["counts"]["critical"],
        "mystictools_doctor_unavailable": doctor["counts"]["unavailable"],
        "mystictools_node_provider_available": 1 if provider["available"] else 0,
        "mystictools_node_provider_qualified": 1 if provider["qualified"] else 0,
        "mystictools_node_fragment_count": provider.get("fragment_count") if fragment_provider else None,
        "mystictools_node_fragment_fresh": provider.get("fresh_fragment_count") if fragment_provider else None,
        "mystictools_node_fragment_stale": provider.get("stale_fragment_count") if fragment_provider else None,
        "mystictools_node_fragment_max_age_seconds": provider.get("max_age_seconds") if fragment_provider else None,
        "mystictools_users_provider_available": 1 if users["available"] else 0,
        "mystictools_users_provider_qualified": 1 if users["qualified"] else 0,
        "mystictools_users_count": users["count"] if users["qualified"] else None,
        "mystictools_users_total_calls": _sum_user_field(users, "calls"),
        "mystictools_users_total_uploads": _sum_user_field(users, "uploads"),
        "mystictools_users_total_downloads": _sum_user_field(users, "downloads"),
        "mystictools_users_total_posts": _sum_user_field(users, "posts"),
        "mystictools_fidonet_config_qualified": 1 if fidonet["qualified_config"] else 0,
        "mystictools_fidonet_busy_files": fidonet["signals"]["busy_count"],
        "mystictools_fidonet_outbound_queue_candidates": fidonet["signals"]["queued_outbound_count"],
        "mystictools_fidonet_inbound_packets": fidonet["signals"]["inbound_packet_count"],
        "mystictools_fidonet_poll_active": (1 if fidonet["poll"]["active"] else 0) if runtime_available else None,
        "mystictools_door_node_temp_dirs": doors["node_temp_count"],
        "mystictools_door_dropfiles": doors["dropfile_count"],
        "mystictools_door_unreadable_dropfiles": doors["unreadable_dropfile_count"],
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "root": str(root),
        "health": health["status"],
        "values": values,
    }


def render_prometheus(snapshot: dict) -> str:
    lines: list[str] = []
    for name, value in snapshot["values"].items():
        if value is None:
            continue
        help_text = _HELP_TEXT.get(name, "MysticTools metric.")
        lines.append(f"# HELP {name} {help_text}")
        lines.append(f"# TYPE {name} gauge")
        lines.append(f"{name} {value}")
    return "\n".join(lines) + "\n"
