import json
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mystictools.backup import MANIFEST_NAME, backup_plan, create_backup


class BackupTests(unittest.TestCase):
    def test_refuses_live_backup_by_default(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "mystic"
            root.mkdir()
            destination = Path(td) / "backup.tar.gz"
            runtime = {"processes": {"available": True, "mis": [{"pid": 1}], "nodes": []}}
            with patch("mystictools.backup.runtime_snapshot", return_value=runtime):
                plan = backup_plan(root, destination)
            self.assertFalse(plan["ok"])
            self.assertEqual(plan["consistency"], "best-effort-live")

    def test_refuses_destination_inside_root(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "mystic"
            root.mkdir()
            runtime = {"processes": {"available": True, "mis": [], "nodes": []}}
            with patch("mystictools.backup.runtime_snapshot", return_value=runtime):
                plan = backup_plan(root, root / "backup.tar.gz")
            self.assertFalse(plan["ok"])
            self.assertIn("outside", " ".join(plan["errors"]))

    def test_offline_backup_contains_manifest_and_payload(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "mystic"
            (root / "data").mkdir(parents=True)
            (root / "data" / "sample.dat").write_bytes(b"MysticTools\n")
            destination = Path(td) / "backup.tar.gz"
            runtime = {"processes": {"available": True, "mis": [], "nodes": []}}
            with patch("mystictools.backup.runtime_snapshot", return_value=runtime):
                result = create_backup(root, destination)
            self.assertTrue(result["ok"])
            self.assertTrue(result["created"])
            self.assertEqual(result["manifest"]["consistency"], "offline")
            self.assertEqual(result["manifest"]["file_count"], 1)
            self.assertTrue(result["archive_sha256"])
            with tarfile.open(destination, "r:gz") as archive:
                names = archive.getnames()
                self.assertIn("mystic/data/sample.dat", names)
                self.assertIn(MANIFEST_NAME, names)
                payload = json.load(archive.extractfile(MANIFEST_NAME))
                self.assertEqual(payload["schema_version"], 1)
                self.assertEqual(payload["files"][0]["path"], "data/sample.dat")


if __name__ == "__main__":
    unittest.main()
