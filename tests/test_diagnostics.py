import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mystictools.diagnostics import (
    EXIT_NOT_FOUND,
    EXIT_OK,
    EXIT_UNAVAILABLE,
    EXIT_WARNING,
    MIN_FREE_BYTES,
    discover_logs,
    disk_snapshot,
    operational_checks,
    permission_snapshot,
)


class DiagnosticsTests(unittest.TestCase):
    def test_exit_code_contract_is_stable(self):
        self.assertEqual(EXIT_OK, 0)
        self.assertEqual(EXIT_WARNING, 1)
        self.assertEqual(EXIT_NOT_FOUND, 2)
        self.assertEqual(EXIT_UNAVAILABLE, 3)

    def test_permission_snapshot_reports_root_owner(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            result = permission_snapshot(root)
            stat = root.stat()
            self.assertEqual(result["root_owner"], {"uid": stat.st_uid, "gid": stat.st_gid})
            self.assertTrue(result["items"]["root"]["readable"])

    def test_log_discovery_finds_log_and_txt_candidates(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            logs = root / "logs"
            logs.mkdir()
            (logs / "mis.log").write_text("x", encoding="utf-8")
            (logs / "server.txt").write_text("x", encoding="utf-8")
            (logs / "ignore.bin").write_bytes(b"x")
            (root / "mystic.log").write_text("x", encoding="utf-8")
            result = discover_logs(root)
            self.assertEqual(result["count"], 3)

    def test_disk_snapshot_marks_low_space(self):
        usage = os.statvfs_result((4096, 4096, 1000, 100, 100, 0, 0, 0, 255, 255))
        with tempfile.TemporaryDirectory() as td:
            with patch("mystictools.diagnostics.shutil.disk_usage") as mocked:
                mocked.return_value = type("Usage", (), {
                    "total": MIN_FREE_BYTES * 4,
                    "used": MIN_FREE_BYTES * 3 + 1,
                    "free": MIN_FREE_BYTES - 1,
                })()
                result = disk_snapshot(Path(td))
            self.assertTrue(result["low_space"])

    def test_operational_checks_warn_without_log_directory(self):
        with tempfile.TemporaryDirectory() as td:
            result = operational_checks(Path(td))
            names = {item["name"] for item in result["checks"] if item["status"] == "warning"}
            self.assertIn("logs:discovery", names)


if __name__ == "__main__":
    unittest.main()
