import os
import stat
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mystictools.backup import create_backup
from mystictools.restore import verify_backup


class BackupHardeningTests(unittest.TestCase):
    def _runtime(self):
        return {"processes": {"available": True, "mis": [], "nodes": []}}

    def test_archive_payload_matches_manifest_and_self_verifies(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            root = base / "mystic"
            (root / "data" / "nested").mkdir(parents=True)
            (root / "data" / "one.dat").write_bytes(b"one")
            (root / "data" / "nested" / "two.dat").write_bytes(b"two")
            destination = base / "backup.tar.gz"

            with patch("mystictools.backup.runtime_snapshot", return_value=self._runtime()):
                result = create_backup(root, destination)

            self.assertTrue(result["ok"])
            self.assertTrue(result["created"])
            verification = verify_backup(destination)
            self.assertTrue(verification["ok"], verification["errors"])
            with tarfile.open(destination, "r:gz") as archive:
                payload = {m.name for m in archive.getmembers() if m.name.startswith("mystic/") and not m.isdir()}
            declared = {f"mystic/{item['path']}" for item in result["manifest"]["files"]}
            self.assertEqual(payload, declared)

    def test_rejects_symlink_escaping_root(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            root = base / "mystic"
            root.mkdir()
            outside = base / "secret.txt"
            outside.write_text("secret", encoding="utf-8")
            os.symlink(outside, root / "outside-link")
            destination = base / "backup.tar.gz"

            with patch("mystictools.backup.runtime_snapshot", return_value=self._runtime()):
                result = create_backup(root, destination)

            self.assertFalse(result["ok"])
            self.assertFalse(result["created"])
            self.assertFalse(destination.exists())
            self.assertTrue(any("symlink target escapes" in item for item in result["errors"]))

    def test_rejects_special_fifo(self):
        if not hasattr(os, "mkfifo"):
            self.skipTest("mkfifo unavailable")
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            root = base / "mystic"
            root.mkdir()
            os.mkfifo(root / "unsafe.fifo")
            destination = base / "backup.tar.gz"

            with patch("mystictools.backup.runtime_snapshot", return_value=self._runtime()):
                result = create_backup(root, destination)

            self.assertFalse(result["ok"])
            self.assertFalse(destination.exists())
            self.assertTrue(any("unsupported special file" in item for item in result["errors"]))

    def test_published_archive_is_owner_only(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            root = base / "mystic"
            root.mkdir()
            (root / "sample.dat").write_bytes(b"sample")
            destination = base / "backup.tar.gz"

            with patch("mystictools.backup.runtime_snapshot", return_value=self._runtime()):
                result = create_backup(root, destination)

            self.assertTrue(result["created"])
            mode = stat.S_IMODE(destination.stat().st_mode)
            self.assertEqual(mode, 0o600)

    def test_internal_relative_symlink_is_preserved(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            root = base / "mystic"
            (root / "data").mkdir(parents=True)
            (root / "data" / "target.dat").write_bytes(b"target")
            os.symlink("target.dat", root / "data" / "link.dat")
            destination = base / "backup.tar.gz"

            with patch("mystictools.backup.runtime_snapshot", return_value=self._runtime()):
                result = create_backup(root, destination)

            self.assertTrue(result["created"], result.get("errors"))
            verification = verify_backup(destination)
            self.assertTrue(verification["ok"], verification["errors"])
            symlinks = [item for item in result["manifest"]["files"] if item["type"] == "symlink"]
            self.assertEqual(symlinks, [{"path": "data/link.dat", "type": "symlink", "target": "target.dat"}])


if __name__ == "__main__":
    unittest.main()
