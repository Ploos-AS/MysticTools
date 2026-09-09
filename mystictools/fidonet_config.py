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


def _read_ini(root: Path) -> tuple[Path | None, dict[str, str]]:
    candidates = (root / "mystictools-fidonet.ini", root / "cfg" / "mystictools-fidonet.ini")
    for path in candidates:
        if not path.is_file():
            continue
        parser = configparser.ConfigParser()
        try:
            with path.open("r", encoding="utf-8") as handle:
                parser.read_file(handle)
        except (OSError, configparser.Error, UnicodeError):
            continue
        if not parser.has_section("paths"):
            return path, {}
        values = {name: parser.get("paths", name, fallback="").strip() for name in _ENV_MAP}
        return path, {name: value for name, value in values.items() if value}
    return None, {}


def fidonet_config(root: Path) -> dict:
    defaults = _default_paths(root)
    ini_path, ini_values = _read_ini(root)
    entries = {}

    for name, default in defaults.items():
        env_name = _ENV_MAP[name]
        env_value = os.environ.get(env_name, "").strip()
        if env_value:
            value = Path(env_value).expanduser()
            source = "environment"
            qualified = True
            source_detail = env_name
        elif name in ini_values:
            value = Path(ini_values[name]).expanduser()
            if not value.is_absolute():
                value = root / value
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
        "qualified_config": all(item["qualified"] for item in entries.values()),
        "paths": entries,
    }
