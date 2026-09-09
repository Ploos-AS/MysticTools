import io
import json
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mystictools.backup import MANIFEST_NAME
from mystictools.restore import restore_preflight, verify_backup


class RestoreTests(unittest.TestCase):
    def _make_archive(self, base: Path, *, payload: bytes = b"hello") -> Path:
        archive_path = base / "backup.tar.gz"
        manifest = {
            "schema_version": 1,
            "created_at": 1,
            "source_root": "/srv/mystic",
            "consistency": "offline",
            "runtime_available": True,
            "bbs_running": False,
            "file_count": 1,
            "files": [
                {
                    "path": "data/test.txt",
                    "type": "file",
                    "size": len(payload),
                    "mode": 0o644,
                    "mtime": 1,
                    "sha256": __import__("hashlib").sha256(payload).hexdigest(),
                }
            ],
        }
        with tarfile.open(archive_path, "w:gz") as archive:
            info = tarfile.TarInfo("mystic/data/test.txt")
            info.size = len(payload)
            archive.addfile(info, io.BytesIO(payload))
            encoded = (json.dumps(manifest) + "\n").encode()
            info = tarfile.TarInfo(MANIFEST_NAME)
            info.size = len(encoded)
            archive.addfile(info, io.BytesIO(encoded))
        return archive_path

    def test_verify_good_archive(self):
        with tempfile.TemporaryDirectory() as td:
            archive = self._make_archive(Path(td))
            result = verify_backup(archive)
            self.assertTrue(result["ok"])
            self.assertEqual(result["verified_files"], 1)

    def test_verify_detects_checksum_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            archive = self._make_archive(base, payload=b"hello")
            with tarfile.open(archive, "r:gz") as source:
                manifest = json.loads(source.extractfile(MANIFEST_NAME).read().decode())
            manifest["files"][0]["sha256"] = "0" * 64
            broken = base / "broken.tar.gz"
            with tarfile.open(broken, "w:gz") as out:
                payload = b"hello"
                info = tarfile.TarInfo("mystic/data/test.txt")
                info.size = len(payload)
                out.addfile(info, io.BytesIO(payload))
                encoded = json.dumps(manifest).encode()
                info = tarfile.TarInfo(MANIFEST_NAME)
                info.size = len(encoded)
                out.addfile(info, io.BytesIO(encoded))
            result = verify_backup(broken)
            self.assertFalse(result["ok"])
            self.assertTrue(any("checksum mismatch" in item for item in result["errors"]))

    def test_verify_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            archive = base / "unsafe.tar.gz"
            manifest = {"schema_version": 1, "file_count": 0, "files": [], "consistency": "offline"}
            with tarfile.open(archive, "w:gz") as out:
                payload = b"x"
                info = tarfile.TarInfo("../escape")
                info.size = 1
                out.addfile(info, io.BytesIO(payload))
                encoded = json.dumps(manifest).encode()
                info = tarfile.TarInfo(MANIFEST_NAME)
                info.size = len(encoded)
                out.addfile(info, io.BytesIO(encoded))
            result = verify_backup(archive)
            self.assertFalse(result["ok"])
            self.assertTrue(any("unsafe archive path" in item for item in result["errors"]))

    def test_preflight_requires_stopped_bbs(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            root = base / "mystic"
            root.mkdir()
            archive = self._make_archive(base)
            runtime = {
                "processes": {"available": True, "mis": [{"pid": 1}], "nodes": []},
                "mis_running": True,
                "active_process_count": 0,
                "version": {"version": None, "build": None, "source": None},
            }
            with patch("mystictools.restore.runtime_snapshot", return_value=runtime):
                result = restore_preflight(root, archive)
            self.assertFalse(result["ok"])
            self.assertTrue(any("processes are running" in item for item in result["errors"]))


if __name__ == "__main__":
    unittest.main()
