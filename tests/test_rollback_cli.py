import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mystictools.rollback_cli import main


class RollbackCliTests(unittest.TestCase):
    def _stopped_runtime(self):
        return {
            "processes": {"available": True, "mis": [], "nodes": []},
            "mis_running": False,
            "active_process_count": 0,
            "version": {"version": None, "build": None, "source": None},
        }

    def test_list_recovery_trees(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "mystic"
            root.mkdir()
            (Path(td) / ".mystic.rollback-1").mkdir()
            with patch("mystictools.rollback_cli.detect_root", return_value=root):
                self.assertEqual(main(["--list"]), 0)

    def test_execute_rollback(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            root = base / "mystic"
            root.mkdir()
            (root / "new.txt").write_text("new", encoding="utf-8")
            rollback = base / ".mystic.rollback-1"
            rollback.mkdir()
            (rollback / "old.txt").write_text("old", encoding="utf-8")
            with patch("mystictools.rollback_cli.detect_root", return_value=root), patch(
                "mystictools.restore.runtime_snapshot", return_value=self._stopped_runtime()
            ):
                self.assertEqual(main([str(rollback), "--execute"]), 0)
            self.assertEqual((root / "old.txt").read_text(encoding="utf-8"), "old")


if __name__ == "__main__":
    unittest.main()
