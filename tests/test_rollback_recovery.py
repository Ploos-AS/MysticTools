import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mystictools.restore_transaction import journal_path, recovery_status, write_journal
from mystictools.rollback import execute_rollback, rollback_preflight


class RollbackRecoveryTests(unittest.TestCase):
    def _stopped_runtime(self):
        return {
            "processes": {"available": True, "mis": [], "nodes": []},
            "mis_running": False,
            "active_process_count": 0,
            "version": {"version": None, "build": None, "source": None},
        }

    def test_old_moved_journal_allows_recorded_rollback_and_clears_journal(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            root = base / "mystic"
            rollback = base / ".mystic.rollback-recorded"
            rollback.mkdir()
            (rollback / "old.txt").write_text("old", encoding="utf-8")
            stage = base / ".mystic.restore-staged"
            write_journal(
                root,
                state="old-moved",
                archive=base / "backup.tar.gz",
                archive_sha256="a" * 64,
                stage=stage,
                rollback=rollback,
            )

            status = recovery_status(root)
            self.assertTrue(status["valid"])
            self.assertEqual(status["classification"], "old-root-moved-new-root-not-installed")
            self.assertEqual(status["recommended_action"], "restore-recorded-rollback")

            with patch("mystictools.rollback.runtime_snapshot", return_value=self._stopped_runtime()):
                result = execute_rollback(root, rollback)

            self.assertTrue(result["ok"])
            self.assertTrue(result["rolled_back"])
            self.assertTrue(result["transaction_journal_cleared"])
            self.assertFalse(journal_path(root).exists())
            self.assertEqual((root / "old.txt").read_text(encoding="utf-8"), "old")

    def test_unfinished_journal_blocks_unrelated_rollback_tree(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            root = base / "mystic"
            root.mkdir()
            recorded = base / ".mystic.rollback-recorded"
            recorded.mkdir()
            unrelated = base / ".mystic.rollback-unrelated"
            unrelated.mkdir()
            write_journal(
                root,
                state="new-installed",
                archive=base / "backup.tar.gz",
                archive_sha256="b" * 64,
                stage=None,
                rollback=recorded,
            )

            with patch("mystictools.rollback.runtime_snapshot", return_value=self._stopped_runtime()):
                result = rollback_preflight(root, unrelated)

            self.assertFalse(result["ok"])
            self.assertFalse(result["journal_matches_rollback"])
            self.assertTrue(any("unrelated recovery tree" in item for item in result["errors"]))

    def test_successful_rollback_preserves_replaced_root_under_unique_failed_tree(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            root = base / "mystic"
            root.mkdir()
            (root / "new.txt").write_text("new", encoding="utf-8")
            rollback = base / ".mystic.rollback-safe"
            rollback.mkdir()
            (rollback / "old.txt").write_text("old", encoding="utf-8")

            with patch("mystictools.rollback.runtime_snapshot", return_value=self._stopped_runtime()):
                result = execute_rollback(root, rollback)

            self.assertTrue(result["ok"])
            failed = Path(result["failed_tree_path"])
            self.assertTrue(failed.name.startswith(".mystic.failed-"))
            self.assertTrue(failed.is_dir())
            self.assertEqual((failed / "new.txt").read_text(encoding="utf-8"), "new")
            self.assertEqual((root / "old.txt").read_text(encoding="utf-8"), "old")

    def test_invalid_journal_path_is_not_trusted(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            root = base / "mystic"
            path = journal_path(root)
            path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "updated_at": 1,
                        "state": "old-moved",
                        "root": str(root),
                        "archive": str(base / "backup.tar.gz"),
                        "archive_sha256": "c" * 64,
                        "stage": str(base / ".mystic.restore-stage"),
                        "rollback": "/tmp/not-a-mystic-sibling",
                    }
                ),
                encoding="utf-8",
            )
            status = recovery_status(root)
            self.assertTrue(status["exists"])
            self.assertFalse(status["valid"])
            self.assertEqual(status["classification"], "invalid-journal")
            self.assertEqual(status["recommended_action"], "inspect-manually")


if __name__ == "__main__":
    unittest.main()
