import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mystictools.recovery_state import read_state, record_event, recovery_tree_counts, state_path


class RecoveryStateTests(unittest.TestCase):
    def test_record_and_read_event(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "mystic"
            root.mkdir()
            with patch("mystictools.recovery_state.time.time", return_value=100):
                record_event(root, "backup", True, consistency="offline")
            result = read_state(root, now=160)
            self.assertTrue(result["qualified"])
            self.assertTrue(result["state"]["events"]["backup"]["success"])
            self.assertEqual(result["ages"]["backup"], 60)

    def test_invalid_state_is_unqualified(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "mystic"
            root.mkdir()
            state_path(root).write_text(json.dumps({"schema_version": 99}), encoding="utf-8")
            result = read_state(root)
            self.assertTrue(result["available"])
            self.assertFalse(result["qualified"])

    def test_recovery_tree_counts(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "mystic"
            root.mkdir()
            (Path(td) / ".mystic.rollback-1").mkdir()
            (Path(td) / ".mystic.failed-2").mkdir()
            counts = recovery_tree_counts(root)
            self.assertEqual(counts, {"rollback": 1, "failed": 1, "total": 2})


if __name__ == "__main__":
    unittest.main()
