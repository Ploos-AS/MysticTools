from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from mystictools.doors import doors_snapshot


class DoorDiagnosticsTests(unittest.TestCase):
    def test_discovers_node_temp_dirs_and_dropfiles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            temp1 = root / "temp1"
            temp2 = root / "TEMP2"
            temp1.mkdir()
            temp2.mkdir()
            (temp1 / "DOOR.SYS").write_text("door\n")
            (temp1 / "CHAIN.TXT").write_text("chain\n")
            (temp2 / "door32.sys").write_text("door32\n")
            (root / "temp-not-a-node").mkdir()

            snap = doors_snapshot(root)

            self.assertEqual(snap["node_temp_count"], 2)
            self.assertEqual(snap["dropfile_count"], 3)
            self.assertEqual([item["node"] for item in snap["nodes"]], [1, 2])
            self.assertEqual(snap["nodes"][0]["dropfile_count"], 2)
            self.assertIn("door-sys", snap["nodes"][0]["formats"])
            self.assertIn("door32-sys", snap["nodes"][1]["formats"])
            self.assertTrue(snap["qualified"])
            self.assertTrue(snap["read_only"])

    def test_ignores_unrelated_files_and_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "temp3").mkdir()
            (root / "temp3" / "random.txt").write_text("x")
            (root / "logs").mkdir()

            snap = doors_snapshot(root)

            self.assertEqual(snap["node_temp_count"], 1)
            self.assertEqual(snap["dropfile_count"], 0)
            self.assertEqual(snap["nodes"][0]["dropfiles"], [])


if __name__ == "__main__":
    unittest.main()
