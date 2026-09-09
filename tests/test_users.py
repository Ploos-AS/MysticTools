import json
import tempfile
import unittest
from pathlib import Path

from mystictools.users import users_snapshot


class UsersTests(unittest.TestCase):
    def test_missing_snapshot_is_unavailable(self):
        with tempfile.TemporaryDirectory() as td:
            snap = users_snapshot(Path(td))
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
                        "users": [
                            {"id": 2, "handle": "Two", "calls": 4, "email": "hidden@example.invalid"},
                            {"id": 1, "handle": "One", "calls": 9},
                        ],
                    }
                )
            )
            snap = users_snapshot(root)
        self.assertTrue(snap["qualified"])
        self.assertEqual([item["id"] for item in snap["users"]], [1, 2])
        self.assertNotIn("email", snap["users"][1])

    def test_invalid_record_marks_snapshot_unqualified(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "mystictools-users.json").write_text(
                json.dumps({"schema_version": 1, "users": [{"id": 0, "handle": "bad"}]})
            )
            snap = users_snapshot(root)
        self.assertFalse(snap["qualified"])
        self.assertEqual(snap["count"], 0)
        self.assertIn("invalid", snap["error"])


if __name__ == "__main__":
    unittest.main()
