from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .backup import create_backup
from .core import check_installation, detect_root, installation_snapshot
from .diagnostics import EXIT_NOT_FOUND, EXIT_OK, EXIT_UNAVAILABLE, EXIT_WARNING, operational_checks
from .doctor import doctor_snapshot
from .doors import doors_snapshot
from .fidonet import fidonet_snapshot
from .logs import DEFAULT_TAIL, MAX_TAIL, log_snapshot
from .metrics import metrics_snapshot, render_prometheus
from .network import health_snapshot, network_snapshot
from .nodes import nodes_snapshot
from .runtime import runtime_snapshot
from .stats import stats_snapshot
from .users import users_snapshot


def emit(payload: dict, as_json: bool, prometheus: bool = False) -> None:
    if prometheus:
        print(render_prometheus(payload["result"]), end="")
        return
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
        print(f"version: {version['version']} {version['build'] or ''}".rstrip() if version["version"] else "version: unknown")
        print(f"MIS: {'running' if runtime['mis_running'] else 'not detected'}")
        print(f"Mystic processes: {runtime['active_process_count']}")
        disk = payload["operations"]["disk"]
        print(f"disk free: {disk['free_bytes']} bytes ({disk['free_percent']}%)" if disk["available"] else "disk free: unavailable")
        print(f"logs: {payload['operations']['logs']['count']} candidate file(s)")
    elif command == "check":
        print(f"Mystic root: {payload['root']}")
        for item in payload["result"]["checks"]:
            print(f"{item['status'].upper():>7} {item['name']}: {item['detail']}")
        print(f"Warnings: {payload['result']['warning_count']}")
    elif command == "doctor":
        print(f"Mystic root: {payload['root']}")
        result = payload["result"]
        print(f"status: {result['status'].upper()}")
        for item in result["findings"]:
            print(f"{item['status'].upper():>11} {item['name']}: {item['detail']}")
        counts = result["counts"]
        print(f"Summary: ok={counts['ok']} warning={counts['warning']} critical={counts['critical']} unavailable={counts['unavailable']}")
    elif command == "backup":
        result = payload["result"]
        print(f"Mystic root: {payload['root']}")
        print(f"destination: {result['destination']}")
        print(f"consistency: {result['consistency']}")
        for warning in result.get("warnings", []):
            print(f"WARNING: {warning}")
        for error in result.get("errors", []):
            print(f"ERROR: {error}")
        if result.get("created"):
            print(f"files: {result['manifest']['file_count']}")
            print(f"archive size: {result['archive_size']} bytes")
            print(f"sha256: {result['archive_sha256']}")
    elif command == "who":
        print(f"Mystic root: {payload['root']}")
        nodes = payload["nodes"]
        if not nodes:
            print("No Mystic node processes detected.")
            return
        for item in nodes:
            node = item["node"] if item["node"] is not None else "?"
            args = " ".join(item["argv"][1:])
            print(f"node={node} pid={item['pid']}{' ' + args if args else ''}")
        if any(item["node"] is None for item in nodes):
            print("Note: '?' means Mystic selected the node internally; MysticTools does not guess it.")
    elif command == "nodes":
        print(f"Mystic root: {payload['root']}")
        result = payload["result"]
        if not result["nodes"]:
            print("No Mystic node records detected.")
            return
        for item in result["nodes"]:
            node = item["node"] if item["node"] is not None else "?"
            runtime = f"{item['runtime_seconds']}s" if item["runtime_seconds"] is not None else "?"
            pid = item["pid"] if item["pid"] is not None else "?"
            print(f"node={node} pid={pid} runtime={runtime} exe={item['exe'] or '?'}")
            if item["arguments"]:
                print(f"  args: {' '.join(item['arguments'])}")
            native = item.get("native")
            if item.get("native_qualified") and native:
                fields = [
                    f"user={native['user']}" if native.get("user") is not None else None,
                    f"action={native['action']}" if native.get("action") is not None else None,
                    f"server={native['server']}" if native.get("server") is not None else None,
                ]
                text = " ".join(field for field in fields if field)
                if text:
                    print(f"  native: {text}")
    elif command == "users":
        print(f"Mystic root: {payload['root']}")
        result = payload["result"]
        print(f"source: {result['source']} (qualified={result['qualified']})")
        if not result["users"]:
            print("No qualified Mystic user records available.")
            return
        for user in result["users"]:
            fields = [f"id={user['id']}"]
            if user.get("handle") is not None:
                fields.append(f"handle={user['handle']}")
            if user.get("security_level") is not None:
                fields.append(f"level={user['security_level']}")
            if user.get("calls") is not None:
                fields.append(f"calls={user['calls']}")
            if user.get("last_on") is not None:
                fields.append(f"last_on={user['last_on']}")
            print(" ".join(fields))
    elif command == "stats":
        print(f"Mystic root: {payload['root']}")
        result = payload["result"]
        for section, names in (("Users", ("users", "calls", "uploads", "downloads", "posts")), ("Runtime", ("mis_running", "node_processes", "listeners"))):
            print(f"{section}:")
            bucket = result[section.lower()]
            for name in names:
                value = bucket[name]
                print(f"  {name}: {value if value is not None else 'unavailable'}")
        for section in ("fidonet", "doors"):
            print(f"{section.title()}:")
            for name, value in result[section].items():
                print(f"  {name}: {value if value is not None else 'unavailable'}")
    elif command == "logs":
        print(f"Mystic root: {payload['root']}")
        result = payload["result"]
        if not result["files"]:
            print(f"No discovered log matched: {result['selector']}" if result["selector"] else "No candidate Mystic log files discovered.")
            return
        for entry in result["files"]:
            print(f"==> {entry['path']} <==")
            if not entry["available"]:
                print(f"[unavailable] {entry['error']}")
                continue
            for line in entry["lines"]:
                print(line)
    elif command == "network":
        print(f"Mystic root: {payload['root']}")
        result = payload["result"]
        if not result["available"]:
            print("Network procfs unavailable.")
            return
        if not result["listeners"]:
            print("No listeners owned by detected MIS/Mystic processes.")
            return
        for item in result["listeners"]:
            print(f"{item['kind']} pid={item['pid']} {item['family']} {item['address']}:{item['port']}")
    elif command == "health":
        print(f"Mystic root: {payload['root']}")
        result = payload["result"]
        print(f"status: {result['status'].upper()}")
        for item in result["checks"]:
            print(f"{item['status'].upper():>7} {item['name']}: {item['detail']}")
    elif command == "metrics":
        print(f"Mystic root: {payload['root']}")
        result = payload["result"]
        print(f"schema: {result['schema_version']}")
        print(f"health: {result['health']}")
        for name, value in result["values"].items():
            print(f"{name}={value if value is not None else 'unavailable'}")
    elif command == "fidonet":
        print(f"Mystic root: {payload['root']}")
        result = payload["result"]
        print(f"source: {result['source']} (qualified_config={result['qualified_config']})")
        for name, item in result["paths"].items():
            state = "present" if item["exists"] else "missing"
            qualification = "qualified" if item.get("qualified") else item.get("source", "derived")
            print(f"{name}: {state} [{qualification}] ({item['path']})")
        signals = result["signals"]
        print(f"busy files: {signals['busy_count']}")
        print(f"queued outbound: {signals['queued_outbound_count']}")
        print(f"inbound packets: {signals['inbound_packet_count']}")
        active = [name for name in ("echomail_in", "echomail_out", "netmail_out") if signals[name]]
        print(f"semaphores: {', '.join(active) if active else 'none'}")
        poll = result["poll"]
        print(f"MIS POLL: {'active' if poll['active'] else 'not detected'} ({poll['count']} process(es))")
        for process in poll["processes"]:
            print(f"  pid={process['pid']} argv={' '.join(process['argv'])}")
    elif command == "doors":
        print(f"Mystic root: {payload['root']}")
        result = payload["result"]
        print(f"node temp dirs: {result['node_temp_count']}")
        print(f"dropfiles: {result['dropfile_count']}")
        for node in result["nodes"]:
            print(f"node={node['node']} path={node['path']} dropfiles={node['dropfile_count']}")
            for item in node["dropfiles"]:
                state = "readable" if item["readable"] else "unreadable"
                print(f"  {item['name']} format={item['kind']} size={item['size']} {state}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="mystictools")
    p.add_argument("--version", action="version", version=__version__)
    p.add_argument("--root", help="Mystic installation root")
    p.add_argument("--json", action="store_true", help="emit JSON")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("status", help="show Mystic installation and runtime status")
    sub.add_parser("check", help="run read-only installation and operational checks")
    sub.add_parser("doctor", help="run cross-source consistency diagnostics")
    backup = sub.add_parser("backup", help="create a checksummed Mystic backup archive")
    backup.add_argument("destination", help="new .tar.gz archive path outside the Mystic root")
    backup.add_argument("--allow-live", action="store_true", help="allow best-effort backup while Mystic/MIS is running")
    backup.add_argument("--allow-unverified", action="store_true", help="allow backup when runtime state cannot be verified")
    sub.add_parser("who", help="show detected Mystic node processes")
    sub.add_parser("nodes", help="show detailed Mystic node/session process information")
    sub.add_parser("users", help="show qualified privacy-safe Mystic user snapshot")
    sub.add_parser("stats", help="show aggregated Mystic BBS statistics")
    sub.add_parser("network", help="show listeners owned by detected MIS/Mystic processes")
    sub.add_parser("health", help="show monitoring-friendly Mystic health summary")
    sub.add_parser("fidonet", help="show conservative FidoNet filesystem and poll diagnostics")
    sub.add_parser("doors", help="show node temp directories and known door dropfiles")
    metrics = sub.add_parser("metrics", help="show exporter-friendly Mystic metrics")
    metrics.add_argument("--prometheus", action="store_true", help="emit Prometheus exposition text")
    logs = sub.add_parser("logs", help="read discovered Mystic log files")
    logs.add_argument("name", nargs="?", help="log filename or stem selector, for example mis")
    logs.add_argument("--tail", type=int, default=DEFAULT_TAIL, help=f"show last N matching lines (0-{MAX_TAIL})")
    logs.add_argument("--contains", help="case-insensitive substring filter")
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "metrics" and args.json and args.prometheus:
        parser.error("--json and metrics --prometheus are mutually exclusive")

    root = detect_root(args.root)
    if root is None:
        payload = {"command": args.command, "ok": False, "error": "Mystic installation not found"}
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(payload["error"], file=sys.stderr)
        return EXIT_NOT_FOUND

    prometheus = False
    if args.command == "status":
        runtime = runtime_snapshot(root)
        operations = operational_checks(root)
        payload = {"command": "status", "ok": True, "root": str(root), "installation": installation_snapshot(root), "runtime": runtime, "operations": operations}
        exit_code = EXIT_OK if runtime["processes"]["available"] else EXIT_UNAVAILABLE
    elif args.command == "check":
        install = check_installation(root)
        operations = operational_checks(root)
        checks = install["checks"] + operations["checks"]
        warning_count = sum(1 for item in checks if item["status"] != "ok")
        result = {"ok": warning_count == 0, "root": str(root), "checks": checks, "warning_count": warning_count, "installation": install, "operations": operations}
        payload = {"command": "check", "ok": result["ok"], "root": str(root), "result": result}
        exit_code = EXIT_OK if result["ok"] else EXIT_WARNING
    elif args.command == "doctor":
        result = doctor_snapshot(root)
        payload = {"command": "doctor", "ok": result["status"] == "ok", "root": str(root), "result": result}
        exit_code = EXIT_OK if result["status"] == "ok" else EXIT_WARNING if result["status"] == "warning" else EXIT_UNAVAILABLE
    elif args.command == "backup":
        result = create_backup(root, Path(args.destination), allow_live=args.allow_live, allow_unverified=args.allow_unverified)
        payload = {"command": "backup", "ok": result["ok"] and result.get("created", False), "root": str(root), "result": result}
        exit_code = EXIT_OK if payload["ok"] else EXIT_WARNING
    elif args.command == "who":
        runtime = runtime_snapshot(root)
        payload = {"command": "who", "ok": runtime["processes"]["available"], "root": str(root), "nodes": runtime["processes"]["nodes"], "source": runtime["processes"]["source"], "source_available": runtime["processes"]["available"]}
        exit_code = EXIT_OK if payload["ok"] else EXIT_UNAVAILABLE
    elif args.command == "nodes":
        result = nodes_snapshot(root)
        payload = {"command": "nodes", "ok": result["available"], "root": str(root), "result": result}
        exit_code = EXIT_OK if result["available"] else EXIT_UNAVAILABLE
    elif args.command == "users":
        result = users_snapshot(root)
        payload = {"command": "users", "ok": result["qualified"], "root": str(root), "result": result}
        exit_code = EXIT_OK if result["qualified"] else EXIT_UNAVAILABLE
    elif args.command == "stats":
        result = stats_snapshot(root)
        available = any((result["sources"]["users_qualified"], result["sources"]["runtime_available"], result["sources"]["network_available"]))
        payload = {"command": "stats", "ok": available, "root": str(root), "result": result}
        exit_code = EXIT_OK if available else EXIT_UNAVAILABLE
    elif args.command == "network":
        runtime = runtime_snapshot(root)
        result = network_snapshot(runtime["processes"])
        payload = {"command": "network", "ok": result["available"], "root": str(root), "result": result}
        exit_code = EXIT_OK if result["available"] else EXIT_UNAVAILABLE
    elif args.command == "health":
        runtime = runtime_snapshot(root)
        network = network_snapshot(runtime["processes"])
        result = health_snapshot(runtime, network)
        payload = {"command": "health", "ok": result["status"] == "ok", "root": str(root), "result": result}
        exit_code = EXIT_OK if result["status"] == "ok" else EXIT_WARNING if result["status"] == "warning" else EXIT_UNAVAILABLE
    elif args.command == "metrics":
        result = metrics_snapshot(root)
        payload = {"command": "metrics", "ok": result["values"]["mystictools_runtime_available"] == 1, "root": str(root), "result": result}
        prometheus = args.prometheus
        exit_code = EXIT_OK if payload["ok"] else EXIT_UNAVAILABLE
    elif args.command == "fidonet":
        runtime = runtime_snapshot(root)
        result = fidonet_snapshot(root, processes=runtime["processes"])
        payload = {"command": "fidonet", "ok": True, "root": str(root), "result": result}
        exit_code = EXIT_OK if runtime["processes"]["available"] else EXIT_UNAVAILABLE
    elif args.command == "doors":
        result = doors_snapshot(root)
        payload = {"command": "doors", "ok": result["unreadable_dropfile_count"] == 0, "root": str(root), "result": result}
        exit_code = EXIT_OK if payload["ok"] else EXIT_WARNING
    else:
        try:
            result = log_snapshot(root, name=args.name, tail=args.tail, contains=args.contains)
        except ValueError as exc:
            if args.json:
                print(json.dumps({"command": "logs", "ok": False, "error": str(exc)}, indent=2, sort_keys=True))
            else:
                print(str(exc), file=sys.stderr)
            return EXIT_WARNING
        payload = {"command": "logs", "ok": result["ok"], "root": str(root), "result": result}
        exit_code = EXIT_OK if result["ok"] else EXIT_UNAVAILABLE

    emit(payload, args.json, prometheus=prometheus)
    return exit_code
