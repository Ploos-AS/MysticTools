from __future__ import annotations

from pathlib import Path

from .diagnostics import operational_checks
from .doors import doors_snapshot
from .fidonet import fidonet_snapshot
from .node_provider import load_node_snapshot
from .network import network_snapshot
from .runtime import runtime_snapshot
from .users import users_snapshot

SCHEMA_VERSION = 1

_SEVERITY = {"ok": 0, "warning": 1, "unavailable": 2, "critical": 3}


def _finding(name: str, status: str, detail: str) -> dict:
    return {"name": name, "status": status, "detail": detail}


def doctor_snapshot(
    root: Path,
    *,
    runtime: dict | None = None,
    network: dict | None = None,
    operations: dict | None = None,
    node_provider: dict | None = None,
    users: dict | None = None,
    fidonet: dict | None = None,
    doors: dict | None = None,
) -> dict:
    runtime = runtime_snapshot(root) if runtime is None else runtime
    processes = runtime["processes"]
    runtime_available = bool(processes["available"])
    network = network_snapshot(processes) if network is None else network
    operations = operational_checks(root) if operations is None else operations
    node_provider = load_node_snapshot(root) if node_provider is None else node_provider
    users = users_snapshot(root) if users is None else users
    fidonet = fidonet_snapshot(root, processes=processes) if fidonet is None else fidonet
    doors = doors_snapshot(root) if doors is None else doors

    findings: list[dict] = []

    if runtime_available:
        findings.append(_finding("runtime", "ok", "Linux procfs runtime discovery is available."))
        if runtime["mis_running"]:
            findings.append(_finding("mis", "ok", "MIS process detected."))
        else:
            findings.append(_finding("mis", "warning", "MIS process was not detected."))
    else:
        findings.append(_finding("runtime", "unavailable", "Linux procfs runtime discovery is unavailable."))

    if network["available"]:
        findings.append(_finding("network", "ok", f"Network discovery available; {len(network['listeners'])} listener(s) mapped."))
    else:
        findings.append(_finding("network", "unavailable", "Network procfs discovery is unavailable."))

    operational_items = operations.get("checks", [])
    critical_operational = [item for item in operational_items if item.get("status") == "critical"]
    if critical_operational:
        findings.append(_finding("operations", "critical", f"{len(critical_operational)} critical operational finding(s) detected."))
    elif operations.get("warning_count", 0):
        findings.append(_finding("operations", "warning", f"{operations['warning_count']} operational warning(s) detected."))
    else:
        findings.append(_finding("operations", "ok", "No operational warnings detected."))

    if node_provider["available"] and not node_provider["qualified"]:
        findings.append(_finding("node_provider", "warning", node_provider.get("error") or "Native node provider is not qualified."))
    elif node_provider["qualified"]:
        stale = node_provider.get("stale_fragment_count", 0)
        status = "warning" if stale else "ok"
        detail = f"Native node provider qualified; {stale} stale fragment(s)." if stale else "Native node provider qualified."
        findings.append(_finding("node_provider", status, detail))
    else:
        findings.append(_finding("node_provider", "warning", "No native node provider snapshot is available."))

    if users["available"] and not users["qualified"]:
        findings.append(_finding("users_provider", "warning", users.get("error") or "Users provider is not qualified."))
    elif users["qualified"]:
        findings.append(_finding("users_provider", "ok", f"Users provider qualified with {users['count']} record(s)."))
    else:
        findings.append(_finding("users_provider", "warning", "No qualified users snapshot is available."))

    if fidonet["qualified_config"]:
        findings.append(_finding("fidonet_config", "ok", "FidoNet paths are explicitly qualified."))
    else:
        config_error = (fidonet.get("config") or {}).get("config_error")
        findings.append(_finding("fidonet_config", "warning", config_error or "FidoNet paths include unqualified/default configuration."))
    if not fidonet.get("qualified_scan", True):
        errors = fidonet.get("scan_errors") or []
        detail = f"FidoNet filesystem scan degraded with {len(errors)} error(s)."
        findings.append(_finding("fidonet_scan", "warning", detail))
    if fidonet["signals"]["busy_count"]:
        findings.append(_finding("fidonet_busy", "warning", f"{fidonet['signals']['busy_count']} FidoNet busy/control file(s) detected."))
    else:
        findings.append(_finding("fidonet_busy", "ok", "No FidoNet busy/control files detected."))

    door_scan_errors = doors.get("scan_errors") or []
    if not doors.get("qualified", True) or door_scan_errors:
        findings.append(_finding("doors_scan", "warning", f"Door filesystem scan degraded with {len(door_scan_errors)} error(s)."))
    if doors["unreadable_dropfile_count"]:
        findings.append(_finding("doors", "warning", f"{doors['unreadable_dropfile_count']} unreadable door dropfile(s) detected."))
    else:
        findings.append(_finding("doors", "ok", "No unreadable known door dropfiles detected."))

    status = max((item["status"] for item in findings), key=lambda value: _SEVERITY[value], default="ok")
    counts = {name: sum(1 for item in findings if item["status"] == name) for name in _SEVERITY}
    return {
        "schema_version": SCHEMA_VERSION,
        "root": str(root),
        "status": status,
        "counts": counts,
        "findings": findings,
    }
