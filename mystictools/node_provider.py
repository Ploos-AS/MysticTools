from __future__ import annotations

import json
import os
import time
from pathlib import Path

SCHEMA_VERSION = 1
DEFAULT_FILENAME = "mystictools-nodes.json"
DEFAULT_FRAGMENT_DIR = "mystictools-nodes.d"
DEFAULT_FRAGMENT_MAX_AGE_SECONDS = 300


def provider_path(root: Path) -> tuple[Path, str]:
    override = os.environ.get("MYSTICTOOLS_NODE_SNAPSHOT")
    if override:
        return Path(override), "environment"
    return root / DEFAULT_FILENAME, "sidecar-default"


def fragment_dir(root: Path) -> tuple[Path, str]:
    override = os.environ.get("MYSTICTOOLS_NODE_FRAGMENT_DIR")
    if override:
        path = Path(override)
        if not path.is_absolute():
            path = root / path
        return path, "fragment-environment"
    return root / DEFAULT_FRAGMENT_DIR, "fragment-default"


def fragment_max_age_seconds() -> int:
    value = os.environ.get("MYSTICTOOLS_NODE_MAX_AGE")
    if value is None:
        return DEFAULT_FRAGMENT_MAX_AGE_SECONDS
    try:
        parsed = int(value)
    except ValueError:
        return DEFAULT_FRAGMENT_MAX_AGE_SECONDS
    return max(1, parsed)


def _normalize_nodes(records: object) -> list[dict]:
    if not isinstance(records, list):
        return []
    nodes = []
    for record in records:
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
    return nodes


def _load_fragments(root: Path, now: float | None = None) -> dict:
    directory, source = fragment_dir(root)
    max_age = fragment_max_age_seconds()
    current_time = time.time() if now is None else now
    if not directory.is_dir():
        return {
            "available": False,
            "qualified": False,
            "source": source,
            "path": str(directory),
            "schema_version": None,
            "nodes": [],
            "error": None,
            "fragment_count": 0,
            "fresh_fragment_count": 0,
            "stale_fragment_count": 0,
            "max_age_seconds": max_age,
        }

    nodes_by_number: dict[int, dict] = {}
    errors: list[str] = []
    stale_count = 0
    fresh_count = 0
    try:
        entries = sorted(directory.glob("node-*.json"))
    except OSError as exc:
        return {
            "available": True,
            "qualified": False,
            "source": source,
            "path": str(directory),
            "schema_version": None,
            "nodes": [],
            "error": str(exc),
            "fragment_count": 0,
            "fresh_fragment_count": 0,
            "stale_fragment_count": 0,
            "max_age_seconds": max_age,
        }

    for path in entries:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{path.name}: {exc}")
            continue
        if payload.get("schema_version") != SCHEMA_VERSION:
            errors.append(f"{path.name}: unsupported schema")
            continue
        generated_at = payload.get("generated_at")
        if not isinstance(generated_at, (int, float)):
            errors.append(f"{path.name}: missing generated_at")
            continue
        age_seconds = max(0.0, current_time - float(generated_at))
        if age_seconds > max_age:
            stale_count += 1
            continue
        normalized = _normalize_nodes(payload.get("nodes"))
        if len(normalized) != 1:
            errors.append(f"{path.name}: expected exactly one node record")
            continue
        record = normalized[0]
        record["generated_at"] = generated_at
        record["age_seconds"] = int(age_seconds)
        nodes_by_number[record["node"]] = record
        fresh_count += 1

    nodes = [nodes_by_number[number] for number in sorted(nodes_by_number)]
    return {
        "available": bool(entries),
        "qualified": bool(nodes) and not errors,
        "source": source,
        "path": str(directory),
        "schema_version": SCHEMA_VERSION if nodes else None,
        "nodes": nodes,
        "error": "; ".join(errors) if errors else None,
        "fragment_count": len(entries),
        "fresh_fragment_count": fresh_count,
        "stale_fragment_count": stale_count,
        "max_age_seconds": max_age,
    }


def load_node_snapshot(root: Path, now: float | None = None) -> dict:
    path, source = provider_path(root)
    if not path.is_file():
        return _load_fragments(root, now=now)
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

    return {
        "available": True,
        "qualified": True,
        "source": source,
        "path": str(path),
        "schema_version": SCHEMA_VERSION,
        "nodes": _normalize_nodes(payload["nodes"]),
        "error": None,
    }


def merge_native_nodes(process_nodes: list[dict], provider: dict) -> list[dict]:
    native_by_node = {item["node"]: item for item in provider.get("nodes", []) if item.get("node") is not None}
    explicit_process_nodes = {item.get("node") for item in process_nodes if item.get("node") is not None}
    has_unknown_process_nodes = any(item.get("node") is None for item in process_nodes)
    merged = []
    seen = set()
    for process in process_nodes:
        item = dict(process)
        node = item.get("node")
        native = native_by_node.get(node) if node is not None else None
        item["native"] = native
        item["native_qualified"] = native is not None and provider.get("qualified", False)
        item["native_active"] = True if native is not None else None
        item["native_correlation"] = "explicit-node-match" if native is not None else "none"
        merged.append(item)
        if node is not None:
            seen.add(node)
    for node, native in sorted(native_by_node.items()):
        if node in seen:
            continue
        if has_unknown_process_nodes:
            active = None
            correlation = "unresolved-auto-selected-process"
        elif node not in explicit_process_nodes:
            active = False
            correlation = "no-matching-process"
        else:
            active = None
            correlation = "unresolved"
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
                "native_active": active,
                "native_correlation": correlation,
            }
        )
    return merged
