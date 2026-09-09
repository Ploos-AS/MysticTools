import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from mystictools.cli import main


class StatsCliTests(unittest.TestCase):
    def test_stats_human_output(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            snapshot = {
                "schema_version": 1,
                "root": str(root),
                "sources": {
                    "users_qualified": True,
                    "runtime_available": True,
                    "network_available": True,
                    "fidonet_config_qualified": False,
                },
                "users": {"users": 3, "calls": 30, "uploads": 4, "downloads": 5, "posts": 6},
                "runtime": {"mis_running": True, "node_processes": 2, "listeners": 3},
                "fidonet": {
                    "busy_files": 0,
                    "outbound_queue_candidates": 1,
                    "inbound_packets": 2,
                    "poll_active": False,
                },
                "doors": {"node_temp_dirs": 2, "dropfiles": 4, "unreadable_dropfiles": 0},
            }
            output = io.StringIO()
            with patch("mystictools.cli.detect_root", return_value=root), patch(
                "mystictools.cli.stats_snapshot", return_value=snapshot
            ), redirect_stdout(output):
                code = main(["stats"])

        self.assertEqual(code, 0)
        text = output.getvalue()
        self.assertIn("users: 3", text)
        self.assertIn("calls: 30", text)
        self.assertIn("node_processes: 2", text)
        self.assertIn("outbound_queue_candidates: 1", text)


if __name__ == "__main__":
    unittest.main()
