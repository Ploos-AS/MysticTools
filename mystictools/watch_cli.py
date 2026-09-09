from __future__ import annotations

import argparse
import json
import os
import sys
import time

from .core import detect_root
from .diagnostics import EXIT_NOT_FOUND, EXIT_OK, EXIT_WARNING
from .watch import render_watch, watch_snapshot


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mysticwatch")
    parser.add_argument("--root", help="Mystic installation root")
    parser.add_argument("--interval", type=float, default=2.0, help="refresh interval in seconds (minimum 0.5)")
    parser.add_argument("--count", type=int, help="stop after N refreshes")
    parser.add_argument("--once", action="store_true", help="render one snapshot and exit")
    parser.add_argument("--no-clear", action="store_true", help="do not clear the terminal between refreshes")
    parser.add_argument("--json", action="store_true", help="emit one JSON snapshot; implies --once")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.interval < 0.5:
        parser.error("--interval must be at least 0.5 seconds")
    if args.count is not None and args.count < 1:
        parser.error("--count must be at least 1")

    root = detect_root(args.root)
    if root is None:
        print("Mystic installation not found", file=sys.stderr)
        return EXIT_NOT_FOUND

    limit = 1 if args.once or args.json else args.count
    rendered = 0
    try:
        while True:
            snapshot = watch_snapshot(root)
            if args.json:
                print(json.dumps(snapshot, indent=2, sort_keys=True))
            else:
                if not args.no_clear and sys.stdout.isatty():
                    print("\033[2J\033[H", end="")
                print(render_watch(snapshot), end="", flush=True)
            rendered += 1
            if limit is not None and rendered >= limit:
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        return EXIT_OK
    except OSError as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_WARNING
    return EXIT_OK
