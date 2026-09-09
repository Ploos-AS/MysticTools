import json
import tempfile
import unittest
from pathlib import Path

from mystictools.users import users_snapshot


class UsersTests(unittest.TestCase):
    def test_missing_snapshot_is_unavailable(self):
        with tempfile.TemporaryDirectory() as td:
            snap = users_snapshot(Path(td), now=1000)
        self.assertFalse(snap["available"])
        self.assertFalse(snap["qualified"])
        self.assertEqual(snap["count"], 0)

    def test_valid_snapshot_is_qualified_and_sorted(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "mystictools-users.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "generated_at": 123,
                        "max_user_id_scanned": 2,
                        "users": [
                            {"id": 2, "handle": "Two", "calls": 4, "email": "hidden@example.invalid"},
                            {"id": 1, "handle": "One", "calls": 9},
                        ],
                    }
                )
            )
            snap = users_snapshot(root, now=130)
        self.assertTrue(snap["qualified"])
        self.assertTrue(snap["fresh"])
        self.assertTrue(snap["complete_scan"])
        self.assertEqual([item["id"] for item in snap["users"]], [1, 2])
        self.assertNotIn("email", snap["users"][1])

    def test_invalid_record_marks_snapshot_unqualified(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "mystictools-users.json").write_text(
                json.dumps({"schema_version": 1, "generated_at": 100, "max_user_id_scanned": 1, "users": [{"id": 0, "handle": "bad"}]})
            )
            snap = users_snapshot(root, now=101)
        self.assertFalse(snap["qualified"])
        self.assertEqual(snap["count"], 0)
        self.assertIn("invalid", snap["error"])

    def test_duplicate_user_ids_are_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "mystictools-users.json").write_text(
                json.dumps({"schema_version": 1, "generated_at": 100, "max_user_id_scanned": 2, "users": [{"id": 1}, {"id": 1}]})
            )
            snap = users_snapshot(root, now=101)
        self.assertFalse(snap["qualified"])
        self.assertIn("duplicate user id", snap["error"])

    def test_future_snapshot_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "mystictools-users.json").write_text(
                json.dumps({"schema_version": 1, "generated_at": 200, "max_user_id_scanned": 1, "users": [{"id": 1}]})
            )
            snap = users_snapshot(root, now=100)
        self.assertFalse(snap["qualified"])
        self.assertFalse(snap["fresh"])
        self.assertIn("future", snap["error"])

    def test_invalid_numeric_type_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "mystictools-users.json").write_text(
                json.dumps({"schema_version": 1, "generated_at": 100, "max_user_id_scanned": 1, "users": [{"id": 1, "calls": "9"}]})
            )
            snap = users_snapshot(root, now=101)
        self.assertFalse(snap["qualified"])
        self.assertIn("calls", snap["error"])


if __name__ == "__main__":
    unittest.main()
