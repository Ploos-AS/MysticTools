from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path

JOURNAL_SCHEMA_VERSION = 1


def journal_path(root: Path) -> Path:
    root = root.resolve()
    return root.parent / f".{root.name}.restore-transaction.json"


def write_journal(root: Path, *, state: str, archive: Path, archive_sha256: str, stage: Path | None, rollback: Path | None) -> Path:
    path = journal_path(root)
    payload = {
        "schema_version": JOURNAL_SCHEMA_VERSION,
        "updated_at": int(time.time()),
        "state": state,
        "root": str(root),
        "archive": str(archive),
        "archive_sha256": archive_sha256,
        "stage": str(stage) if stage is not None else None,
        "rollback": str(rollback) if rollback is not None else None,
    }
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temp = Path(temp_name)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
        os.chmod(path, 0o600)
        return path
    except Exception:
        try:
            os.close(fd)
        except OSError:
            pass
        temp.unlink(missing_ok=True)
        raise


def clear_journal(root: Path) -> None:
    journal_path(root).unlink(missing_ok=True)
