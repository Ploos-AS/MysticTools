from __future__ import annotations

import time
from pathlib import Path

from .doors import doors_snapshot
from .fidonet import fidonet_snapshot
from .metrics import metrics_snapshot
from .network import network_snapshot
from .nodes import nodes_snapshot
from .recovery_state import read_state, recovery_tree_counts
from .runtime import runtime_snapshot


def watch_snapshot(root: Path) -> dict:
    root = root.resolve()
    runtime = runtime_snapshot(root)
    processes = runtime["processes"]
    nodes = nodes_snapshot(root)
    network = network_snapshot(processes)
    fidonet = fidonet_snapshot(root, processes=processes)
    doors = doors_snapshot(root)
    recovery = read_state(root)
    recovery_trees = recovery_tree_counts(root)
    metrics = metrics_snapshot(root)
    return {
        "root": str(root),
        "timestamp": int(time.time()),
        "runtime": {
            "available": bool(processes["available"]),
            "mis_running": runtime["mis_running"] if processes["available"] else None,
            "node_processes": runtime["active_process_count"] if processes["available"] else None,
        },
        "nodes": nodes,
        "network": network,
        "fidonet": fidonet,
        "doors": doors,
        "recovery": recovery,
        "recovery_trees": recovery_trees,
        "health": metrics["health"],
        "metrics_schema": metrics["schema_version"],
    }


def render_watch(snapshot: dict) -> str:
    runtime = snapshot["runtime"]
    nodes = snapshot["nodes"]
    network = snapshot["network"]
    fidonet = snapshot["fidonet"]
    doors = snapshot["doors"]
    recovery = snapshot["recovery"]
    trees = snapshot["recovery_trees"]

    lines = [
        f"MysticTools watch — {snapshot['root']}",
        f"health={snapshot['health']} runtime={'available' if runtime['available'] else 'unavailable'} ",
        f"MIS={'running' if runtime['mis_running'] else 'stopped' if runtime['mis_running'] is False else 'unknown'} nodes={runtime['node_processes'] if runtime['node_processes'] is not None else '?'} listeners={len(network['listeners']) if network['available'] else '?'}",
        "",
        "Nodes:",
    ]
    if nodes["nodes"]:
        for item in nodes["nodes"]:
            node = item["node"] if item["node"] is not None else "?"
            pid = item["pid"] if item["pid"] is not None else "?"
            action = ((item.get("native") or {}).get("action") if item.get("native_qualified") else None) or "-"
            user = ((item.get("native") or {}).get("user") if item.get("native_qualified") else None) or "-"
            lines.append(f"  node={node} pid={pid} user={user} action={action}")
    else:
        lines.append("  none")

    lines.extend([
        "",
        "FidoNet:",
        f"  poll={'active' if fidonet['poll']['active'] else 'idle'} busy={fidonet['signals']['busy_count']} outbound={fidonet['signals']['queued_outbound_count']} inbound={fidonet['signals']['inbound_packet_count']}",
        "Doors:",
        f"  temp_dirs={doors['node_temp_count']} dropfiles={doors['dropfile_count']} unreadable={doors['unreadable_dropfile_count']}",
        "Recovery:",
        f"  state={'qualified' if recovery['qualified'] else 'unavailable' if not recovery['available'] else 'unqualified'} rollback_trees={trees['rollback']} failed_trees={trees['failed']}",
        f"Prometheus schema={snapshot['metrics_schema']}",
    ])
    return "\n".join(lines) + "\n"
