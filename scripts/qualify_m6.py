#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

READ_ONLY_COMMANDS = (
    "status",
    "check",
    "who",
    "nodes",
    "users",
    "stats",
    "network",
    "health",
    "doctor",
    "fidonet",
    "doors",
    "metrics",
)


def run_json(root: Path, command: str) -> dict:
    proc = subprocess.run(
        [sys.executable, "-m", "mystictools", "--root", str(root), "--json", command],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    parsed = None
    error = None
    if proc.stdout.strip():
        try:
            parsed = json.loads(proc.stdout)
        except json.JSONDecodeError as exc:
            error = f"invalid JSON output: {exc}"
    return {
        "command": command,
        "exit_code": proc.returncode,
        "ok": proc.returncode == 0,
        "payload": parsed,
        "stderr": proc.stderr.strip() or None,
        "error": error,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect M6.0 MysticTools runtime qualification evidence")
    parser.add_argument("--root", required=True, type=Path, help="real Mystic installation root")
    parser.add_argument("--output", type=Path, default=Path("m6-runtime-qualification.json"))
    parser.add_argument("--require-node-provider", action="store_true")
    parser.add_argument("--require-users-provider", action="store_true")
    args = parser.parse_args()

    root = args.root.expanduser().resolve()
    results = [run_json(root, command) for command in READ_ONLY_COMMANDS]
    by_command = {item["command"]: item for item in results}

    assertions = []

    def record(name: str, passed: bool, detail: str) -> None:
        assertions.append({"name": name, "passed": bool(passed), "detail": detail})

    status = by_command["status"]
    record("status-json", status["payload"] is not None, "status emitted parseable JSON")
    if status["payload"]:
        runtime = status["payload"].get("runtime") or {}
        version = runtime.get("version") or {}
        record("mystic-version-detected", bool(version.get("version")), f"version={version.get('version')!r}")

    nodes = (by_command["nodes"]["payload"] or {}).get("result") or {}
    provider = nodes.get("native_provider") or {}
    if args.require_node_provider:
        record("node-provider-qualified", provider.get("qualified") is True, provider.get("error") or str(provider.get("source")))

    users = (by_command["users"]["payload"] or {}).get("result") or {}
    if args.require_users_provider:
        record("users-provider-qualified", users.get("qualified") is True, users.get("error") or f"count={users.get('count')}")
        record("users-provider-fresh", users.get("fresh") is True, f"age_seconds={users.get('age_seconds')}")
        record("users-provider-complete-scan", users.get("complete_scan") is True, f"max_user_id_scanned={users.get('max_user_id_scanned')}")

    fidonet = (by_command["fidonet"]["payload"] or {}).get("result") or {}
    record("fidonet-scan-qualified", fidonet.get("qualified_scan") is True, str(fidonet.get("scan_errors")))

    doors = (by_command["doors"]["payload"] or {}).get("result") or {}
    record("doors-scan-qualified", doors.get("qualified") is True, str(doors.get("scan_errors")))

    doctor = (by_command["doctor"]["payload"] or {}).get("result") or {}
    record("doctor-not-critical", doctor.get("status") != "critical", f"status={doctor.get('status')}")

    report = {
        "schema_version": 1,
        "generated_at": int(time.time()),
        "root": str(root),
        "python": sys.version.split()[0],
        "requirements": {
            "node_provider": args.require_node_provider,
            "users_provider": args.require_users_provider,
        },
        "assertions": assertions,
        "results": results,
    }
    report["passed"] = all(item["passed"] for item in assertions) and all(item["error"] is None for item in results)

    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"M6.0 qualification {'PASS' if report['passed'] else 'FAIL'}: {args.output}")
    for item in assertions:
        print(f"{'PASS' if item['passed'] else 'FAIL'} {item['name']}: {item['detail']}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
