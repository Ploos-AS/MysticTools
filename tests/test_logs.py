import tempfile
import unittest
from pathlib import Path

from mystictools.logs import log_snapshot, read_log, select_logs


class LogTests(unittest.TestCase):
    def test_select_logs_by_name(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            logs = root / "logs"
            logs.mkdir()
            (logs / "mis.log").write_text("one\n", encoding="utf-8")
            (logs / "mutil.log").write_text("two\n", encoding="utf-8")
            selected = select_logs(root, "mis")
            self.assertEqual([p.name for p in selected], ["mis.log"])

    def test_tail_and_filter(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "sample.log"
            path.write_text("alpha\nERROR one\nbeta\nerror two\ngamma\n", encoding="utf-8")
            result = read_log(path, tail=1, contains="error")
            self.assertTrue(result["available"])
            self.assertEqual(result["lines"], ["error two"])

    def test_snapshot_reads_all_discovered_logs(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            logs = root / "logs"
            logs.mkdir()
            (logs / "a.log").write_text("A\n", encoding="utf-8")
            (logs / "b.log").write_text("B\n", encoding="utf-8")
            result = log_snapshot(root, tail=10)
            self.assertTrue(result["ok"])
            self.assertEqual(result["file_count"], 2)

    def test_tail_is_bounded(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "sample.log"
            path.write_text("x\n", encoding="utf-8")
            result = read_log(path, tail=999999)
            self.assertTrue(result["available"])

    def test_negative_tail_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "sample.log"
            path.write_text("x\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                read_log(path, tail=-1)


if __name__ == "__main__":
    unittest.main()
