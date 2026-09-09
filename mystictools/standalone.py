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


def _dispatch_argv(command: str, args: list[str]) -> list[str]:
    """Place umbrella-global options before the synthetic subcommand token.

    Standalone commands share the umbrella argparse parser. Options owned by a
    subcommand must therefore remain after the inserted command token, while
    --root/--json/--version stay in the umbrella parser's global position.
    """
    global_args: list[str] = []
    command_args: list[str] = []
    index = 0
    while index < len(args):
        arg = args[index]
        if arg in {"--json", "--version"} or arg.startswith("--root="):
            global_args.append(arg)
            index += 1
            continue
        if arg == "--root":
            global_args.append(arg)
            if index + 1 < len(args):
                global_args.append(args[index + 1])
                index += 2
            else:
                index += 1
            continue
        command_args.append(arg)
        index += 1
    return [*global_args, command, *command_args]


def main(argv: list[str] | None = None) -> int:
    prog = Path(sys.argv[0]).name
    command = COMMANDS.get(prog)
    if command is None:
        raise SystemExit(f"unsupported standalone entry point: {prog}")
    args = list(sys.argv[1:] if argv is None else argv)
    return app_main(_dispatch_argv(command, args))
