from __future__ import annotations

from pathlib import Path

from .runtime import runtime_snapshot


def nodes_snapshot(root: Path) -> dict:
    runtime = runtime_snapshot(root)
    processes = runtime["processes"]
    nodes = []
    for item in processes["nodes"]:
        argv = item.get("argv") or []
        nodes.append(
            {
                "pid": item["pid"],
                "node": item.get("node"),
                "node_source": item.get("node_source"),
                "started_at": item.get("started_at"),
                "runtime_seconds": item.get("runtime_seconds"),
                "exe": item.get("exe"),
                "arguments": argv[1:],
            }
        )
    return {
        "ok": processes["available"],
        "source": processes["source"],
        "count": len(nodes),
        "nodes": nodes,
    }
