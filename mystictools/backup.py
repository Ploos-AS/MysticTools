from __future__ import annotations

import hashlib
import json
import os
import stat
import tarfile
import tempfile
import time
from pathlib import Path

from .runtime import runtime_snapshot

SCHEMA_VERSION = 1
MANIFEST_NAME = "mystictools-backup-manifest.json"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _inside(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _inventory(root: Path) -> tuple[list[dict], list[Path]]:
    files: list[dict] = []
    directories: list[Path] = []

    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        try:
            info = path.lstat()
            mode = info.st_mode
            if stat.S_ISLNK(mode):
                target = os.readlink(path)
                resolved_target = (path.parent / target).resolve(strict=False) if not os.path.isabs(target) else Path(target).resolve(strict=False)
                if not _inside(resolved_target, root):
                    raise OSError(f"symlink target escapes Mystic root: {relative} -> {target}")
                files.append({"path": relative, "type": "symlink", "target": target})
            elif stat.S_ISREG(mode):
                files.append(
                    {
                        "path": relative,
                        "type": "file",
                        "size": info.st_size,
                        "mode": mode & 0o7777,
                        "mtime": int(info.st_mtime),
                        "sha256": _sha256(path),
                    }
                )
            elif stat.S_ISDIR(mode):
                directories.append(path)
            else:
                raise OSError(f"unsupported special file in Mystic root: {relative}")
        except OSError as exc:
            raise OSError(f"unable to inventory {path}: {exc}") from exc

    return files, directories


def backup_plan(root: Path, destination: Path, allow_live: bool = False, allow_unverified: bool = False) -> dict:
    root = root.resolve()
    destination = destination.expanduser().resolve()
    runtime = runtime_snapshot(root)
    processes = runtime["processes"]
    running = bool(processes.get("mis") or processes.get("nodes")) if processes.get("available") else None

    errors: list[str] = []
    warnings: list[str] = []
    if _inside(destination, root):
        errors.append("backup destination must be outside the Mystic root")
    if destination.exists():
        errors.append("backup destination already exists")
    if not processes.get("available"):
        if not allow_unverified:
            errors.append("runtime state is unavailable; use allow_unverified only after independently verifying Mystic is stopped")
        else:
            warnings.append("runtime state unavailable; backup consistency cannot be verified")
    elif running:
        if not allow_live:
            errors.append("Mystic/MIS processes are running; stop the BBS or explicitly allow a live best-effort backup")
        else:
            warnings.append("live backup requested; application-level consistency is not guaranteed")

    return {
        "ok": not errors,
        "root": str(root),
        "destination": str(destination),
        "runtime_available": bool(processes.get("available")),
        "bbs_running": running,
        "consistency": "best-effort-live" if running else ("offline" if running is False else "unverified"),
        "errors": errors,
        "warnings": warnings,
    }


def create_backup(root: Path, destination: Path, allow_live: bool = False, allow_unverified: bool = False) -> dict:
    plan = backup_plan(root, destination, allow_live=allow_live, allow_unverified=allow_unverified)
    if not plan["ok"]:
        return {**plan, "created": False, "manifest": None}

    root = Path(plan["root"])
    destination = Path(plan["destination"])
    destination.parent.mkdir(parents=True, exist_ok=True)

    started = int(time.time())
    try:
        files, directories = _inventory(root)
    except OSError as exc:
        return {**plan, "ok": False, "created": False, "manifest": None, "errors": [str(exc)]}

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "created_at": started,
        "source_root": str(root),
        "consistency": plan["consistency"],
        "runtime_available": plan["runtime_available"],
        "bbs_running": plan["bbs_running"],
        "file_count": sum(1 for item in files if item["type"] == "file"),
        "files": files,
    }

    fd, temporary_name = tempfile.mkstemp(prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent)
    os.close(fd)
    temporary = Path(temporary_name)
    os.chmod(temporary, 0o600)

    try:
        with tempfile.TemporaryDirectory() as td:
            manifest_path = Path(td) / MANIFEST_NAME
            manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            os.chmod(manifest_path, 0o600)

            with tarfile.open(temporary, "w:gz", format=tarfile.PAX_FORMAT, dereference=False) as archive:
                archive.add(root, arcname="mystic", recursive=False)
                for directory in directories:
                    relative = directory.relative_to(root).as_posix()
                    archive.add(directory, arcname=f"mystic/{relative}", recursive=False)
                for record in files:
                    source = root / record["path"]
                    archive.add(source, arcname=f"mystic/{record['path']}", recursive=False)
                archive.add(manifest_path, arcname=MANIFEST_NAME, recursive=False)

        os.chmod(temporary, 0o600)

        # Verify exactly what was written before publishing the archive.  The
        # import is intentionally local to avoid a module-level backup/restore
        # cycle while reusing the authoritative restore verifier.
        from .restore import verify_backup

        verification = verify_backup(temporary)
        if not verification["ok"]:
            errors = [f"backup self-verification failed: {item}" for item in verification["errors"]]
            temporary.unlink(missing_ok=True)
            return {**plan, "ok": False, "created": False, "manifest": manifest, "errors": errors}

        os.replace(temporary, destination)
        os.chmod(destination, 0o600)
    except (OSError, tarfile.TarError) as exc:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        return {**plan, "ok": False, "created": False, "manifest": manifest, "errors": [str(exc)]}

    return {
        **plan,
        "created": True,
        "manifest": manifest,
        "archive_size": destination.stat().st_size,
        "archive_sha256": _sha256(destination),
    }
