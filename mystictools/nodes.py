from __future__ import annotations

from pathlib import Path

from .node_provider import load_node_snapshot, merge_native_nodes
from .runtime import runtime_snapshot


def nodes_snapshot(root: Path) -> dict:
    runtime = runtime_snapshot(root)
    processes = runtime["processes"]
    process_nodes = []
    for item in processes["nodes"]:
        argv = item.get("argv") or []
        process_nodes.append(
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

    provider = load_node_snapshot(root)
    nodes = merge_native_nodes(process_nodes, provider) if provider["qualified"] else [
        {**item, "native": None, "native_qualified": False} for item in process_nodes
    ]

    return {
        "ok": processes["available"],
        "available": processes["available"],
        "source": processes["source"],
        "count": len(nodes),
        "nodes": nodes,
        "native_provider": provider,
    }
