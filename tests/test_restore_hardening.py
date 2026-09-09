import hashlib
import io
import json
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mystictools.backup import MANIFEST_NAME
from mystictools.restore import execute_restore, verify_backup


class RestoreHardeningTests(unittest.TestCase):
    def _manifest(self, records):
        return {
            "schema_version": 1,
            "created_at": 1,
            "source_root": "/srv/mystic",
            "consistency": "offline",
            "runtime_available": True,
            "bbs_running": False,
            "file_count": sum(1 for record in records if record["type"] == "file"),
            "files": records,
        }

    def _add_manifest(self, archive, manifest):
        encoded = json.dumps(manifest).encode()
        info = tarfile.TarInfo(MANIFEST_NAME)
        info.size = len(encoded)
        archive.addfile(info, io.BytesIO(encoded))

    def _file_record(self, path, payload=b"hello"):
        return {
            "path": path,
            "type": "file",
            "size": len(payload),
            "mode": 0o644,
            "mtime": 1,
            "sha256": hashlib.sha256(payload).hexdigest(),
        }

    def _stopped_runtime(self):
        return {
            "processes": {"available": True, "mis": [], "nodes": []},
            "mis_running": False,
            "active_process_count": 0,
            "version": {"version": None, "build": None, "source": None},
        }

    def test_rejects_payload_not_declared_in_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            archive_path = Path(td) / "extra.tar.gz"
            record = self._file_record("data/good.txt")
            with tarfile.open(archive_path, "w:gz") as archive:
                for name, payload in (("mystic/data/good.txt", b"hello"), ("mystic/data/evil.txt", b"evil")):
                    info = tarfile.TarInfo(name)
                    info.size = len(payload)
                    archive.addfile(info, io.BytesIO(payload))
                self._add_manifest(archive, self._manifest([record]))
            result = verify_backup(archive_path)
            self.assertFalse(result["ok"])
            self.assertTrue(any("not declared in manifest" in error for error in result["errors"]))

    def test_rejects_hardlink_member(self):
        with tempfile.TemporaryDirectory() as td:
            archive_path = Path(td) / "hardlink.tar.gz"
            record = self._file_record("data/good.txt")
            with tarfile.open(archive_path, "w:gz") as archive:
                payload = b"hello"
                info = tarfile.TarInfo("mystic/data/good.txt")
                info.size = len(payload)
                archive.addfile(info, io.BytesIO(payload))
                link = tarfile.TarInfo("mystic/data/link.txt")
                link.type = tarfile.LNKTYPE
                link.linkname = "mystic/data/good.txt"
                archive.addfile(link)
                self._add_manifest(archive, self._manifest([record]))
            result = verify_backup(archive_path)
            self.assertFalse(result["ok"])
            self.assertTrue(any("hardlinks are not supported" in error for error in result["errors"]))

    def test_rejects_file_nested_beneath_symlink(self):
        with tempfile.TemporaryDirectory() as td:
            archive_path = Path(td) / "symlink-parent.tar.gz"
            payload = b"owned"
            records = [
                {"path": "data/link", "type": "symlink", "target": "../safe"},
                self._file_record("data/link/owned.txt", payload),
            ]
            with tarfile.open(archive_path, "w:gz") as archive:
                link = tarfile.TarInfo("mystic/data/link")
                link.type = tarfile.SYMTYPE
                link.linkname = "../safe"
                archive.addfile(link)
                info = tarfile.TarInfo("mystic/data/link/owned.txt")
                info.size = len(payload)
                archive.addfile(info, io.BytesIO(payload))
                self._add_manifest(archive, self._manifest(records))
            result = verify_backup(archive_path)
            self.assertFalse(result["ok"])
            self.assertTrue(any("nested beneath a symlink" in error for error in result["errors"]))

    def test_rejects_symlink_target_escaping_root(self):
        with tempfile.TemporaryDirectory() as td:
            archive_path = Path(td) / "symlink-escape.tar.gz"
            records = [{"path": "link", "type": "symlink", "target": "../../outside"}]
            with tarfile.open(archive_path, "w:gz") as archive:
                link = tarfile.TarInfo("mystic/link")
                link.type = tarfile.SYMTYPE
                link.linkname = "../../outside"
                archive.addfile(link)
                self._add_manifest(archive, self._manifest(records))
            result = verify_backup(archive_path)
            self.assertFalse(result["ok"])
            self.assertTrue(any("unsafe symlink target" in error for error in result["errors"]))

    def test_execute_restore_streams_verified_regular_file(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            root = base / "mystic"
            archive_path = base / "good.tar.gz"
            record = self._file_record("data/good.txt")
            with tarfile.open(archive_path, "w:gz") as archive:
                payload = b"hello"
                info = tarfile.TarInfo("mystic/data/good.txt")
                info.size = len(payload)
                archive.addfile(info, io.BytesIO(payload))
                self._add_manifest(archive, self._manifest([record]))
            with patch("mystictools.restore.runtime_snapshot", return_value=self._stopped_runtime()):
                result = execute_restore(root, archive_path)
            self.assertTrue(result["ok"])
            self.assertEqual((root / "data" / "good.txt").read_bytes(), b"hello")


if __name__ == "__main__":
    unittest.main()
