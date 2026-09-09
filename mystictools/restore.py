from __future__ import annotations

import hashlib
import json
import os
import shutil
import tarfile
import tempfile
import time
from pathlib import Path, PurePosixPath

from .backup import MANIFEST_NAME, SCHEMA_VERSION
from .runtime import runtime_snapshot


def _safe_member_name(name: str) -> bool:
    path = PurePosixPath(name)
    return not path.is_absolute() and ".." not in path.parts


def _sha256_stream(handle) -> str:
    digest = hashlib.sha256()
    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
        digest.update(chunk)
    return digest.hexdigest()


def _runtime_guard(root: Path, operation: str) -> tuple[bool, bool | None, list[str]]:
    runtime = runtime_snapshot(root)
    processes = runtime["processes"]
    available = bool(processes.get("available"))
    running = bool(processes.get("mis") or processes.get("nodes")) if available else None
    errors: list[str] = []
    if not available:
        errors.append(f"runtime state is unavailable; {operation} requires verified stopped Mystic/MIS processes")
    elif running:
        errors.append(f"Mystic/MIS processes are running; stop the BBS before {operation}")
    return available, running, errors


def verify_backup(archive_path: Path) -> dict:
    archive_path = archive_path.expanduser().resolve()
    errors: list[str] = []
    warnings: list[str] = []
    manifest: dict | None = None
    verified_files = 0

    if not archive_path.is_file():
        return {"ok": False, "archive": str(archive_path), "manifest": None, "verified_files": 0, "errors": ["backup archive does not exist"], "warnings": []}

    try:
        with tarfile.open(archive_path, "r:gz") as archive:
            members = archive.getmembers()
            names = [member.name for member in members]
            if len(names) != len(set(names)):
                errors.append("archive contains duplicate member names")
            for member in members:
                if not _safe_member_name(member.name):
                    errors.append(f"unsafe archive path: {member.name}")
                if member.issym() or member.islnk():
                    if not _safe_member_name(member.linkname):
                        errors.append(f"unsafe archive link target: {member.name} -> {member.linkname}")

            try:
                manifest_member = archive.getmember(MANIFEST_NAME)
            except KeyError:
                errors.append(f"missing {MANIFEST_NAME}")
                manifest_member = None

            if manifest_member is not None:
                handle = archive.extractfile(manifest_member)
                if handle is None:
                    errors.append("backup manifest is not a regular file")
                else:
                    try:
                        manifest = json.loads(handle.read().decode("utf-8"))
                    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                        errors.append(f"invalid backup manifest: {exc}")

            if manifest is not None:
                if manifest.get("schema_version") != SCHEMA_VERSION:
                    errors.append("unsupported backup manifest schema")
                records = manifest.get("files")
                if not isinstance(records, list):
                    errors.append("backup manifest files field is invalid")
                    records = []

                member_map = {member.name: member for member in members}
                seen_paths: set[str] = set()
                for record in records:
                    if not isinstance(record, dict):
                        errors.append("backup manifest contains invalid file record")
                        continue
                    relative = record.get("path")
                    kind = record.get("type")
                    if not isinstance(relative, str) or not _safe_member_name(relative):
                        errors.append(f"unsafe manifest path: {relative!r}")
                        continue
                    if relative in seen_paths:
                        errors.append(f"duplicate manifest path: {relative}")
                        continue
                    seen_paths.add(relative)
                    member = member_map.get(f"mystic/{relative}")
                    if member is None:
                        errors.append(f"manifest member missing from archive: {relative}")
                        continue
                    if kind == "file":
                        if not member.isfile():
                            errors.append(f"manifest expected file but archive member differs: {relative}")
                            continue
                        if member.size != record.get("size"):
                            errors.append(f"size mismatch: {relative}")
                            continue
                        handle = archive.extractfile(member)
                        if handle is None:
                            errors.append(f"unable to read archive member: {relative}")
                            continue
                        if _sha256_stream(handle) != record.get("sha256"):
                            errors.append(f"checksum mismatch: {relative}")
                            continue
                        verified_files += 1
                    elif kind == "symlink":
                        if not member.issym() or member.linkname != record.get("target"):
                            errors.append(f"symlink target mismatch: {relative}")
                    else:
                        errors.append(f"unsupported manifest record type for {relative}: {kind!r}")

                expected_count = manifest.get("file_count")
                if isinstance(expected_count, int) and expected_count != verified_files:
                    errors.append("manifest file_count does not match verified regular files")
                if manifest.get("consistency") != "offline":
                    warnings.append(f"backup consistency is {manifest.get('consistency')!r}, not 'offline'")
    except (OSError, tarfile.TarError) as exc:
        errors.append(str(exc))

    return {"ok": not errors, "archive": str(archive_path), "manifest": manifest, "verified_files": verified_files, "errors": errors, "warnings": warnings}


def restore_preflight(root: Path, archive_path: Path) -> dict:
    root = root.resolve()
    verification = verify_backup(archive_path)
    runtime_available, bbs_running, runtime_errors = _runtime_guard(root, "restore")
    errors = list(verification["errors"]) + runtime_errors
    warnings = list(verification["warnings"])

    manifest = verification.get("manifest") or {}
    source_root = manifest.get("source_root")
    if source_root and Path(source_root).name != root.name:
        warnings.append("backup source root basename differs from target root")

    return {
        "ok": not errors,
        "root": str(root),
        "archive": verification["archive"],
        "runtime_available": runtime_available,
        "bbs_running": bbs_running,
        "verified_files": verification["verified_files"],
        "manifest": verification.get("manifest"),
        "errors": errors,
        "warnings": warnings,
        "mode": "verify-and-preflight-only",
    }


def execute_restore(root: Path, archive_path: Path, *, replace_existing: bool = False) -> dict:
    root = root.resolve()
    preflight = restore_preflight(root, archive_path)
    if not preflight["ok"]:
        return {**preflight, "restored": False, "rollback_path": None, "mode": "guarded-restore"}

    if root.exists() and not replace_existing:
        return {
            **preflight,
            "ok": False,
            "restored": False,
            "rollback_path": None,
            "mode": "guarded-restore",
            "errors": preflight["errors"] + ["target root already exists; use --replace-existing after reviewing preflight"],
        }

    parent = root.parent
    parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{root.name}.restore-", dir=parent))
    rollback: Path | None = None
    archive_path = Path(preflight["archive"])

    try:
        with tarfile.open(archive_path, "r:gz") as archive:
            for member in archive.getmembers():
                if member.name == MANIFEST_NAME:
                    continue
                if member.name == "mystic" or not member.name.startswith("mystic/"):
                    continue
                relative = PurePosixPath(member.name).relative_to("mystic")
                destination = stage.joinpath(*relative.parts)
                destination.parent.mkdir(parents=True, exist_ok=True)
                if member.isdir():
                    destination.mkdir(parents=True, exist_ok=True)
                elif member.isfile():
                    handle = archive.extractfile(member)
                    if handle is None:
                        raise OSError(f"unable to read archive member: {member.name}")
                    with destination.open("wb") as out:
                        shutil.copyfileobj(handle, out)
                elif member.issym():
                    os.symlink(member.linkname, destination)
                else:
                    raise OSError(f"unsupported archive member type: {member.name}")

        manifest = preflight.get("manifest") or {}
        for record in manifest.get("files", []):
            relative = record.get("path")
            if not isinstance(relative, str):
                continue
            path = stage / relative
            if record.get("type") == "file":
                os.chmod(path, int(record.get("mode", 0o644)))
                mtime = int(record.get("mtime", int(time.time())))
                os.utime(path, (mtime, mtime), follow_symlinks=False)

        for record in manifest.get("files", []):
            if record.get("type") != "file":
                continue
            path = stage / record["path"]
            if not path.is_file():
                raise OSError(f"staged file missing: {record['path']}")
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest != record.get("sha256"):
                raise OSError(f"staged checksum mismatch: {record['path']}")

        if root.exists():
            rollback = parent / f".{root.name}.rollback-{int(time.time())}"
            if rollback.exists():
                raise OSError(f"rollback path already exists: {rollback}")
            os.replace(root, rollback)
        try:
            os.replace(stage, root)
        except OSError:
            if rollback is not None and rollback.exists() and not root.exists():
                os.replace(rollback, root)
                rollback = None
            raise

        return {
            **preflight,
            "ok": True,
            "restored": True,
            "rollback_path": str(rollback) if rollback is not None else None,
            "mode": "guarded-restore",
        }
    except (OSError, tarfile.TarError) as exc:
        if stage.exists():
            shutil.rmtree(stage, ignore_errors=True)
        return {
            **preflight,
            "ok": False,
            "restored": False,
            "rollback_path": str(rollback) if rollback is not None and rollback.exists() else None,
            "mode": "guarded-restore",
            "errors": preflight["errors"] + [str(exc)],
        }


def rollback_preflight(root: Path, rollback_path: Path) -> dict:
    root = root.resolve()
    rollback_path = rollback_path.expanduser().resolve()
    runtime_available, bbs_running, errors = _runtime_guard(root, "rollback")
    warnings: list[str] = []

    expected_prefix = f".{root.name}.rollback-"
    if rollback_path.parent != root.parent:
        errors.append("rollback tree must be a sibling of the Mystic root")
    if not rollback_path.name.startswith(expected_prefix):
        errors.append(f"rollback tree name must start with {expected_prefix!r}")
    if not rollback_path.is_dir():
        errors.append("rollback tree does not exist or is not a directory")
    if not root.exists():
        warnings.append("current target root does not exist; rollback will install the saved tree directly")

    return {
        "ok": not errors,
        "root": str(root),
        "rollback_path": str(rollback_path),
        "runtime_available": runtime_available,
        "bbs_running": bbs_running,
        "errors": errors,
        "warnings": warnings,
        "mode": "rollback-preflight-only",
    }


def execute_rollback(root: Path, rollback_path: Path) -> dict:
    preflight = rollback_preflight(root, rollback_path)
    if not preflight["ok"]:
        return {**preflight, "rolled_back": False, "failed_tree_path": None, "mode": "guarded-rollback"}

    root = Path(preflight["root"])
    rollback_path = Path(preflight["rollback_path"])
    failed_tree: Path | None = None
    try:
        if root.exists():
            failed_tree = root.parent / f".{root.name}.failed-{int(time.time())}"
            if failed_tree.exists():
                raise OSError(f"failed-tree path already exists: {failed_tree}")
            os.replace(root, failed_tree)
        try:
            os.replace(rollback_path, root)
        except OSError:
            if failed_tree is not None and failed_tree.exists() and not root.exists():
                os.replace(failed_tree, root)
                failed_tree = None
            raise
        return {
            **preflight,
            "ok": True,
            "rolled_back": True,
            "failed_tree_path": str(failed_tree) if failed_tree is not None else None,
            "mode": "guarded-rollback",
        }
    except OSError as exc:
        return {
            **preflight,
            "ok": False,
            "rolled_back": False,
            "failed_tree_path": str(failed_tree) if failed_tree is not None and failed_tree.exists() else None,
            "mode": "guarded-rollback",
            "errors": preflight["errors"] + [str(exc)],
        }


def discover_recovery_trees(root: Path) -> dict:
    root = root.resolve()
    parent = root.parent
    rollback_prefix = f".{root.name}.rollback-"
    failed_prefix = f".{root.name}.failed-"
    rollback = sorted(str(path) for path in parent.glob(f"{rollback_prefix}*") if path.is_dir())
    failed = sorted(str(path) for path in parent.glob(f"{failed_prefix}*") if path.is_dir())
    return {
        "root": str(root),
        "rollback_trees": rollback,
        "failed_trees": failed,
        "cleanup_policy": "manual-only",
    }
