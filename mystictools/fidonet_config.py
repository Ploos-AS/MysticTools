from __future__ import annotations

import configparser
import os
from pathlib import Path

_ENV_MAP = {
    "inbound": "MYSTICTOOLS_FIDONET_INBOUND",
    "inbound_unsecured": "MYSTICTOOLS_FIDONET_INBOUND_UNSECURED",
    "outbound_primary": "MYSTICTOOLS_FIDONET_OUTBOUND_PRIMARY",
    "semaphore": "MYSTICTOOLS_FIDONET_SEMAPHORE",
}


def _default_paths(root: Path) -> dict[str, Path]:
    return {
        "inbound": root / "echomail" / "in",
        "inbound_unsecured": root / "echomail" / "in" / "unsecure",
        "outbound_primary": root / "echomail" / "out" / "primary",
        "semaphore": root / "semaphore",
    }


def _read_ini(root: Path) -> tuple[Path | None, dict[str, str], str | None]:
    candidates = (root / "mystictools-fidonet.ini", root / "cfg" / "mystictools-fidonet.ini")
    for path in candidates:
        if not path.is_file():
            continue
        parser = configparser.ConfigParser()
        try:
            with path.open("r", encoding="utf-8") as handle:
                parser.read_file(handle)
        except (OSError, configparser.Error, UnicodeError) as exc:
            return path, {}, f"unable to read FidoNet config {path}: {exc}"
        if not parser.has_section("paths"):
            return path, {}, f"FidoNet config {path} is missing required [paths] section"
        values = {name: parser.get("paths", name, fallback="").strip() for name in _ENV_MAP}
        return path, {name: value for name, value in values.items() if value}, None
    return None, {}, None


def _root_relative(root: Path, value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else root / path


def fidonet_config(root: Path) -> dict:
    root = root.expanduser().resolve()
    defaults = _default_paths(root)
    ini_path, ini_values, config_error = _read_ini(root)
    entries = {}

    for name, default in defaults.items():
        env_name = _ENV_MAP[name]
        env_value = os.environ.get(env_name, "").strip()
        if env_value:
            value = _root_relative(root, env_value)
            source = "environment"
            qualified = True
            source_detail = env_name
        elif name in ini_values:
            value = _root_relative(root, ini_values[name])
            source = "mystictools-ini"
            qualified = True
            source_detail = str(ini_path)
        else:
            value = default
            source = "mystic-default"
            qualified = False
            source_detail = None

        entries[name] = {
            "path": str(value),
            "source": source,
            "source_detail": source_detail,
            "qualified": qualified,
        }

    return {
        "provider": "explicit-overrides-with-default-fallback",
        "config_file": str(ini_path) if ini_path else None,
        "config_error": config_error,
        "qualified_config": config_error is None and all(item["qualified"] for item in entries.values()),
        "paths": entries,
    }
