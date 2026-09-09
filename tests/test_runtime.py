import os
import tempfile
import unittest
from pathlib import Path

from mystictools.runtime import detect_version, discover_processes, parse_node_number


class RuntimeTests(unittest.TestCase):
    def _proc(self, root: Path, pid: int, argv: list[str], exe_target: str):
        proc = root / str(pid)
        proc.mkdir()
        (proc / "cmdline").write_bytes(b"\0".join(a.encode() for a in argv) + b"\0")
        os.symlink(exe_target, proc / "exe")

    def test_parse_node_number(self):
        self.assertEqual(parse_node_number(["mystic", "-N7"]), 7)
        self.assertIsNone(parse_node_number(["mystic", "-IP127.0.0.1"]))

    def test_procfs_discovers_mis_and_mystic(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._proc(root, 101, ["/mystic/mis", "server"], "/mystic/mis")
            self._proc(root, 202, ["/mystic/mystic", "-N3", "-IP192.0.2.1"], "/mystic/mystic")
            result = discover_processes(root)
            self.assertTrue(result["available"])
            self.assertEqual(result["mis"][0]["pid"], 101)
            self.assertEqual(result["nodes"][0]["node"], 3)
            self.assertEqual(result["nodes"][0]["node_source"], "argv")

    def test_auto_selected_node_is_not_guessed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._proc(root, 203, ["/mystic/mystic", "-IP192.0.2.2"], "/mystic/mystic")
            result = discover_processes(root)
            self.assertIsNone(result["nodes"][0]["node"])
            self.assertIsNone(result["nodes"][0]["node_source"])

    def test_version_from_whatsnew_fixture(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "whatsnew.txt").write_text("Mystic BBS 1.12 Alpha A48\n", encoding="utf-8")
            result = detect_version(root)
            self.assertEqual(result["version"], "1.12")
            self.assertEqual(result["build"], "A48")


if __name__ == "__main__":
    unittest.main()
