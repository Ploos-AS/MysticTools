from __future__ import annotations

import sys
from pathlib import Path

from . import cli
from .core import detect_root
from .recovery_state import safe_record_event
from .watch_cli import main as watch_main


def _explicit_root(argv: list[str]) -> str | None:
    for index, arg in enumerate(argv):
        if arg == "--root" and index + 1 < len(argv):
            return argv[index + 1]
        if arg.startswith("--root="):
            return arg.split("=", 1)[1]
    return None


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)

    # `watch` has its own refresh-loop parser but is also exposed through the
    # umbrella command. Preserve global --root/--json arguments by removing
    # only the command token.
    if "watch" in args:
        watch_args = list(args)
        watch_args.remove("watch")
        return watch_main(watch_args)

    exit_code = cli.main(args)

    command = next((arg for arg in args if arg in {"backup", "restore"}), None)
    should_record = command == "backup" or (command == "restore" and "--execute" in args)
    if should_record:
        root = detect_root(_explicit_root(args))
        if root is not None:
            safe_record_event(root, command, exit_code == 0)
    return exit_code
