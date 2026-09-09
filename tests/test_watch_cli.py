import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from mystictools import app
from mystictools.watch_cli import main


class WatchCliTests(unittest.TestCase):
    def _snapshot(self, root: Path) -> dict:
        return {
            "root": str(root),
            "timestamp": 1,
            "health": "ok",
            "metrics_schema": 3,
            "runtime": {"available": True, "mis_running": False, "node_processes": 0},
            "nodes": {"nodes": []},
            "network": {"available": True, "listeners": []},
            "fidonet": {"poll": {"active": False}, "signals": {"busy_count": 0, "queued_outbound_count": 0, "inbound_packet_count": 0}},
            "doors": {"node_temp_count": 0, "dropfile_count": 0, "unreadable_dropfile_count": 0},
            "recovery": {"available": False, "qualified": False},
            "recovery_trees": {"rollback": 0, "failed": 0, "total": 0},
        }

    def test_once_renders_and_exits(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with patch("mystictools.watch_cli.detect_root", return_value=root), patch(
                "mystictools.watch_cli.watch_snapshot", return_value=self._snapshot(root)
            ):
                output = io.StringIO()
                with redirect_stdout(output):
                    rc = main(["--once", "--no-clear"])
        self.assertEqual(rc, 0)
        self.assertIn("MysticTools watch", output.getvalue())

    def test_json_implies_once(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with patch("mystictools.watch_cli.detect_root", return_value=root), patch(
                "mystictools.watch_cli.watch_snapshot", return_value=self._snapshot(root)
            ):
                output = io.StringIO()
                with redirect_stdout(output):
                    rc = main(["--json"])
        self.assertEqual(rc, 0)
        self.assertIn('"health": "ok"', output.getvalue())

    def test_umbrella_routes_watch(self):
        with patch("mystictools.app.watch_main", return_value=0) as watch:
            rc = app.main(["--root", "/srv/mystic", "watch", "--once"])
        self.assertEqual(rc, 0)
        watch.assert_called_once_with(["--root", "/srv/mystic", "--once"])


if __name__ == "__main__":
    unittest.main()
