from __future__ import annotations

import argparse
import json
import sys

from . import __version__
from .core import check_installation, detect_root, installation_snapshot
from .diagnostics import (
    EXIT_NOT_FOUND,
    EXIT_OK,
    EXIT_UNAVAILABLE,
    EXIT_WARNING,
    operational_checks,
)
from .runtime import runtime_snapshot


def emit(payload: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return

    command = payload.get("command")
    if command == "status":
        print(f"Mystic root: {payload['root']}")
        for name, info in payload["installation"]["paths"].items():
            state = "present" if info["exists"] else "missing"
            print(f"{name:>5}: {state} ({info['path']})")
        runtime = payload["runtime"]
        version = runtime["version"]
        if version["version"]:
            print(f"version: {version['version']} {version['build'] or ''}".rstrip())
        else:
            print("version: unknown")
        print(f"MIS: {'running' if runtime['mis_running'] else 'not detected'}")
        print(f"Mystic processes: {runtime['active_process_count']}")
        ops = payload["operations"]
        disk = ops["disk"]
        if disk["available"]:
            print(f"disk free: {disk['free_bytes']} bytes ({disk['free_percent']}%)")
        else:
            print("disk free: unavailable")
        print(f"logs: {ops['logs']['count']} candidate file(s)")
    elif command == "check":
        print(f"Mystic root: {payload['root']}")
        for item in payload["result"]["checks"]:
            print(f"{item['status'].upper():>7} {item['name']}: {item['detail']}")
        print(f"Warnings: {payload['result']['warning_count']}")
    elif command == "who":
        print(f"Mystic root: {payload['root']}")
        nodes = payload["nodes"]
        if not nodes:
            print("No Mystic node processes detected.")
            return
        for item in nodes:
            node = item["node"] if item["node"] is not None else "?"
            args = " ".join(item["argv"][1:])
            suffix = f" {args}" if args else ""
            print(f"node={node} pid={item['pid']}{suffix}")
        if any(item["node"] is None for item in nodes):
            print("Note: '?' means Mystic selected the node internally; MysticTools does not guess it.")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="mystictools")
    p.add_argument("--version", action="version", version=__version__)
    p.add_argument("--root", help="Mystic installation root")
    p.add_argument("--json", action="store_true", help="emit JSON")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("status", help="show Mystic installation and runtime status")
    sub.add_parser("check", help="run read-only installation and operational checks")
    sub.add_parser("who", help="show detected Mystic node processes")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = detect_root(args.root)
    if root is None:
        payload = {"command": args.command, "ok": False, "error": "Mystic installation not found"}
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(payload["error"], file=sys.stderr)
        return EXIT_NOT_FOUND

    if args.command == "status":
        runtime = runtime_snapshot(root)
        operations = operational_checks(root)
        payload = {
            "command": "status",
            "ok": True,
            "root": str(root),
            "installation": installation_snapshot(root),
            "runtime": runtime,
            "operations": operations,
        }
        exit_code = EXIT_OK if runtime["processes"]["available"] else EXIT_UNAVAILABLE
    elif args.command == "check":
        install = check_installation(root)
        operations = operational_checks(root)
        checks = install["checks"] + operations["checks"]
        warning_count = sum(1 for item in checks if item["status"] != "ok")
        result = {
            "ok": warning_count == 0,
            "root": str(root),
            "checks": checks,
            "warning_count": warning_count,
            "installation": install,
            "operations": operations,
        }
        payload = {"command": "check", "ok": result["ok"], "root": str(root), "result": result}
        exit_code = EXIT_OK if result["ok"] else EXIT_WARNING
    else:
        runtime = runtime_snapshot(root)
        payload = {
            "command": "who",
            "ok": runtime["processes"]["available"],
            "root": str(root),
            "nodes": runtime["processes"]["nodes"],
            "source": runtime["processes"]["source"],
            "source_available": runtime["processes"]["available"],
        }
        exit_code = EXIT_OK if payload["ok"] else EXIT_UNAVAILABLE

    emit(payload, args.json)
    return exit_code
