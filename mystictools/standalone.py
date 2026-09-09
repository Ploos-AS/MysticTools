from __future__ import annotations

import sys
from pathlib import Path

from .app import main as app_main


COMMANDS = {
    "mysticstatus": "status",
    "mysticcheck": "check",
    "mysticwho": "who",
    "mysticnodes": "nodes",
    "mysticlog": "logs",
    "mysticnet": "network",
    "mysticfidonet": "fidonet",
    "mysticdoors": "doors",
    "mysticusers": "users",
    "mysticstats": "stats",
    "mystichealth": "health",
    "mysticdoctor": "doctor",
    "mysticbackup": "backup",
    "mysticrestore": "restore",
    "mysticmetrics": "metrics",
}


def main(argv: list[str] | None = None) -> int:
    prog = Path(sys.argv[0]).name
    command = COMMANDS.get(prog)
    if command is None:
        raise SystemExit(f"unsupported standalone entry point: {prog}")
    args = list(sys.argv[1:] if argv is None else argv)
    return app_main([*args, command])
