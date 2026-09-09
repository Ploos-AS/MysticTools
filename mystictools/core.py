from __future__ import annotations

import os
from pathlib import Path

DEFAULT_ROOTS = (Path("/mystic"), Path("/opt/mystic"), Path("/srv/mystic"))


def detect_root(explicit: str | None = None) -> Path | None:
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit).expanduser())
    env_root = os.environ.get("MYSTIC_ROOT")
    if env_root:
        candidates.append(Path(env_root).expanduser())
    candidates.extend(DEFAULT_ROOTS)

    seen: set[Path] = set()
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate in seen:
            continue
        seen.add(candidate)
        if candidate.is_dir():
            return candidate
    return None


def installation_snapshot(root: Path) -> dict:
    expected = {
        "mis": root / "mis",
        "mutil": root / "mutil",
        "cfg": root / "cfg",
        "data": root / "data",
        "logs": root / "logs",
    }
    return {
        "root": str(root),
        "exists": root.is_dir(),
        "paths": {
            name: {
                "path": str(path),
                "exists": path.exists(),
                "executable": path.is_file() and os.access(path, os.X_OK),
            }
            for name, path in expected.items()
        },
    }


def check_installation(root: Path) -> dict:
    snap = installation_snapshot(root)
    checks = []
    for name, item in snap["paths"].items():
        checks.append({
            "name": f"path:{name}",
            "status": "ok" if item["exists"] else "warning",
            "detail": item["path"],
        })
    problems = [c for c in checks if c["status"] != "ok"]
    return {
        "root": str(root),
        "ok": not problems,
        "checks": checks,
        "warning_count": len(problems),
    }
