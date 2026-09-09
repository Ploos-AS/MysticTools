from __future__ import annotations

import argparse
import sys

from .core import detect_root
from .diagnostics import EXIT_NOT_FOUND, EXIT_OK, EXIT_WARNING
from .exporter import DEFAULT_BIND, DEFAULT_PORT, serve


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mysticexporter")
    parser.add_argument("--root", help="Mystic installation root")
    parser.add_argument("--bind", default=DEFAULT_BIND, help=f"listen address (default {DEFAULT_BIND})")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"listen port (default {DEFAULT_PORT})")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not 1 <= args.port <= 65535:
        parser.error("--port must be between 1 and 65535")

    root = detect_root(args.root)
    if root is None:
        print("Mystic installation not found", file=sys.stderr)
        return EXIT_NOT_FOUND

    try:
        print(f"MysticTools exporter: http://{args.bind}:{args.port} root={root}")
        serve(root, args.bind, args.port)
    except KeyboardInterrupt:
        return EXIT_OK
    except OSError as exc:
        print(f"exporter failed: {exc}", file=sys.stderr)
        return EXIT_WARNING
    return EXIT_OK
