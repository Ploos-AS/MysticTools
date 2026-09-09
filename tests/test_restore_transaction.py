import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mystictools.restore import execute_restore
from mystictools.restore_transaction import journal_path, write_journal


class RestoreTransactionTests(unittest.TestCase):
    def _stopped_runtime(self):
        return {
            "processes": {"available": True, "mis": [], "nodes": []},
            "mis_running": False,
            "active_process_count": 0,
            "version": {"version": None, "build": None, "source": None},
        }

    def _make_backup(self, base: Path) -> Path:
        from mystictools.backup import create_backup

        root = base / "source"
        (root / "data").mkdir(parents=True)
        (root / "data" / "test.txt").write_text("hello", encoding="utf-8")
        archive = base / "backup.tar.gz"
        with patch("mystictools.backup.runtime_snapshot", return_value=self._stopped_runtime()):
            result = create_backup(root, archive)
        self.assertTrue(result["ok"])
        return archive

    def test_existing_transaction_journal_blocks_restore(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            root = base / "mystic"
            archive = self._make_backup(base)
            write_journal(root, state="old-moved", archive=archive, archive_sha256="0" * 64, stage=None, rollback=base / ".mystic.rollback-x")
            with patch("mystictools.restore.runtime_snapshot", return_value=self._stopped_runtime()):
                result = execute_restore(root, archive)
            self.assertFalse(result["ok"])
            self.assertEqual(result["transaction_journal"], str(journal_path(root)))
            self.assertTrue(any("unfinished restore transaction" in item for item in result["errors"]))

    def test_successful_restore_clears_transaction_journal(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            root = base / "mystic"
            archive = self._make_backup(base)
            with patch("mystictools.restore.runtime_snapshot", return_value=self._stopped_runtime()):
                result = execute_restore(root, archive)
            self.assertTrue(result["ok"])
            self.assertFalse(journal_path(root).exists())
            self.assertEqual((root / "data" / "test.txt").read_text(encoding="utf-8"), "hello")

    def test_archive_change_during_verification_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            root = base / "mystic"
            archive = self._make_backup(base)
            real_sha = hashlib.sha256(archive.read_bytes()).hexdigest()
            calls = {"archive": 0}

            def fake_sha(path):
                path = Path(path)
                if path == archive:
                    calls["archive"] += 1
                    if calls["archive"] == 2:
                        return "f" * 64 if real_sha != "f" * 64 else "e" * 64
                    return real_sha
                return hashlib.sha256(path.read_bytes()).hexdigest()

            with patch("mystictools.restore.runtime_snapshot", return_value=self._stopped_runtime()), patch("mystictools.restore._sha256_path", side_effect=fake_sha):
                result = execute_restore(root, archive)
            self.assertFalse(result["ok"])
            self.assertTrue(any("changed during verification" in item for item in result["errors"]))
            self.assertFalse(root.exists())
            self.assertFalse(journal_path(root).exists())


if __name__ == "__main__":
    unittest.main()
