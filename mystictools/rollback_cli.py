from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .core import detect_root
from .diagnostics import EXIT_NOT_FOUND, EXIT_OK, EXIT_WARNING
from .restore import discover_recovery_trees, execute_rollback, rollback_preflight


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mysticrollback")
    parser.add_argument("--root", help="Mystic installation root")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument("rollback_path", nargs="?", help="saved .<root>.rollback-* tree")
    parser.add_argument("--list", action="store_true", help="list preserved rollback/failed recovery trees")
    parser.add_argument("--execute", action="store_true", help="perform rollback after successful preflight")
    return parser


def _emit(payload: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    result = payload["result"]
    if payload["command"] == "rollback-list":
        print(f"Mystic root: {payload['root']}")
        print("rollback trees:")
        for path in result["rollback_trees"]:
            print(f"  {path}")
        print("failed trees:")
        for path in result["failed_trees"]:
            print(f"  {path}")
        print(f"cleanup policy: {result['cleanup_policy']}")
        return

    print(f"Mystic root: {payload['root']}")
    print(f"rollback tree: {result['rollback_path']}")
    print(f"mode: {result['mode']}")
    for warning in result.get("warnings", []):
        print(f"WARNING: {warning}")
    for error in result.get("errors", []):
        print(f"ERROR: {error}")
    if result.get("rolled_back"):
        print("rollback: COMPLETE")
        if result.get("failed_tree_path"):
            print(f"preserved replaced tree: {result['failed_tree_path']}")
    else:
        print(f"preflight: {'PASS' if result['ok'] else 'FAIL'}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = detect_root(args.root)
    if root is None:
        if args.json:
            print(json.dumps({"command": "rollback", "ok": False, "error": "Mystic installation not found"}, indent=2, sort_keys=True))
        else:
            print("Mystic installation not found", file=sys.stderr)
        return EXIT_NOT_FOUND

    if args.list:
        if args.rollback_path or args.execute:
            parser.error("--list cannot be combined with rollback_path or --execute")
        result = discover_recovery_trees(root)
        payload = {"command": "rollback-list", "ok": True, "root": str(root), "result": result}
        _emit(payload, args.json)
        return EXIT_OK

    if not args.rollback_path:
        parser.error("rollback_path is required unless --list is used")

    path = Path(args.rollback_path)
    result = execute_rollback(root, path) if args.execute else rollback_preflight(root, path)
    ok = result["ok"] and (result.get("rolled_back", False) if args.execute else True)
    payload = {"command": "rollback", "ok": ok, "root": str(root), "result": result}
    _emit(payload, args.json)
    return EXIT_OK if ok else EXIT_WARNING
