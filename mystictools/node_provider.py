from __future__ import annotations

import json
import os
from pathlib import Path

SCHEMA_VERSION = 1
DEFAULT_FILENAME = "mystictools-nodes.json"


def provider_path(root: Path) -> tuple[Path, str]:
    override = os.environ.get("MYSTICTOOLS_NODE_SNAPSHOT")
    if override:
        return Path(override), "environment"
    return root / DEFAULT_FILENAME, "sidecar-default"


def load_node_snapshot(root: Path) -> dict:
    path, source = provider_path(root)
    if not path.is_file():
        return {
            "available": False,
            "qualified": False,
            "source": source,
            "path": str(path),
            "schema_version": None,
            "nodes": [],
            "error": None,
        }
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "available": True,
            "qualified": False,
            "source": source,
            "path": str(path),
            "schema_version": None,
            "nodes": [],
            "error": str(exc),
        }

    if payload.get("schema_version") != SCHEMA_VERSION or not isinstance(payload.get("nodes"), list):
        return {
            "available": True,
            "qualified": False,
            "source": source,
            "path": str(path),
            "schema_version": payload.get("schema_version"),
            "nodes": [],
            "error": "unsupported or invalid node snapshot schema",
        }

    nodes = []
    for record in payload["nodes"]:
        if not isinstance(record, dict) or not isinstance(record.get("node"), int) or record["node"] < 1:
            continue
        nodes.append(
            {
                "node": record["node"],
                "user": record.get("user"),
                "action": record.get("action"),
                "server": record.get("server"),
                "invisible": record.get("invisible"),
                "available_for_messages": record.get("available_for_messages"),
            }
        )

    return {
        "available": True,
        "qualified": True,
        "source": source,
        "path": str(path),
        "schema_version": SCHEMA_VERSION,
        "nodes": nodes,
        "error": None,
    }


def merge_native_nodes(process_nodes: list[dict], provider: dict) -> list[dict]:
    native_by_node = {item["node"]: item for item in provider.get("nodes", []) if item.get("node") is not None}
    merged = []
    seen = set()
    for process in process_nodes:
        item = dict(process)
        node = item.get("node")
        native = native_by_node.get(node) if node is not None else None
        item["native"] = native
        item["native_qualified"] = native is not None and provider.get("qualified", False)
        merged.append(item)
        if node is not None:
            seen.add(node)
    for node, native in sorted(native_by_node.items()):
        if node in seen:
            continue
        merged.append(
            {
                "pid": None,
                "node": node,
                "node_source": "native-provider",
                "started_at": None,
                "runtime_seconds": None,
                "exe": None,
                "arguments": [],
                "native": native,
                "native_qualified": provider.get("qualified", False),
            }
        )
    return merged
