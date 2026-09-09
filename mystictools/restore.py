from __future__ import annotations

import hashlib
import io
import json
import os
import tarfile
from pathlib import Path, PurePosixPath

from .backup import MANIFEST_NAME, SCHEMA_VERSION
from .runtime import runtime_snapshot


def _safe_member_name(name: str) -> bool:
    path = PurePosixPath(name)
    if path.is_absolute():
        return False
    if ".." in path.parts:
        return False
    return True


def _sha256_stream(handle) -> str:
    digest = hashlib.sha256()
    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
        digest.update(chunk)
    return digest.hexdigest()


def verify_backup(archive_path: Path) -> dict:
    archive_path = archive_path.expanduser().resolve()
    errors: list[str] = []
    warnings: list[str] = []
    manifest: dict | None = None
    verified_files = 0

    if not archive_path.is_file():
        return {
            "ok": False,
            "archive": str(archive_path),
            "manifest": None,
            "verified_files": 0,
            "errors": ["backup archive does not exist"],
            "warnings": [],
        }

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
                    member_name = f"mystic/{relative}"
                    member = member_map.get(member_name)
                    if member is None:
                        errors.append(f"manifest member missing from archive: {relative}")
                        continue

                    if kind == "file":
                        if not member.isfile():
                            errors.append(f"manifest expected file but archive member differs: {relative}")
                            continue
                        expected_size = record.get("size")
                        expected_sha = record.get("sha256")
                        if member.size != expected_size:
                            errors.append(f"size mismatch: {relative}")
                            continue
                        handle = archive.extractfile(member)
                        if handle is None:
                            errors.append(f"unable to read archive member: {relative}")
                            continue
                        actual_sha = _sha256_stream(handle)
                        if actual_sha != expected_sha:
                            errors.append(f"checksum mismatch: {relative}")
                            continue
                        verified_files += 1
                    elif kind == "symlink":
                        if not member.issym():
                            errors.append(f"manifest expected symlink but archive member differs: {relative}")
                            continue
                        if member.linkname != record.get("target"):
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

    return {
        "ok": not errors,
        "archive": str(archive_path),
        "manifest": manifest,
        "verified_files": verified_files,
        "errors": errors,
        "warnings": warnings,
    }


def restore_preflight(root: Path, archive_path: Path) -> dict:
    root = root.resolve()
    verification = verify_backup(archive_path)
    runtime = runtime_snapshot(root)
    processes = runtime["processes"]
    errors = list(verification["errors"])
    warnings = list(verification["warnings"])

    runtime_available = bool(processes.get("available"))
    bbs_running = bool(processes.get("mis") or processes.get("nodes")) if runtime_available else None
    if not runtime_available:
        errors.append("runtime state is unavailable; restore requires verified stopped Mystic/MIS processes")
    elif bbs_running:
        errors.append("Mystic/MIS processes are running; stop the BBS before restore")

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
