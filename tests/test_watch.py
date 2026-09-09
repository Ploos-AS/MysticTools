import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mystictools.watch import render_watch, watch_snapshot


class WatchTests(unittest.TestCase):
    def test_watch_snapshot_aggregates_existing_sources(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            runtime_value = {
                "processes": {"available": True, "mis": [], "nodes": []},
                "mis_running": False,
                "active_process_count": 0,
            }
            provider_value = {"available": False, "qualified": False, "nodes": []}
            with patch("mystictools.watch.runtime_snapshot", return_value=runtime_value), patch(
                "mystictools.watch.load_node_snapshot", return_value=provider_value
            ), patch(
                "mystictools.watch.nodes_snapshot", return_value={"nodes": [], "available": True}
            ) as nodes, patch(
                "mystictools.watch.network_snapshot", return_value={"available": True, "listeners": [{}, {}]}
            ), patch(
                "mystictools.watch.health_snapshot", return_value={"status": "ok", "checks": [], "listener_count": 2}
            ), patch(
                "mystictools.watch.fidonet_snapshot",
                return_value={"poll": {"active": False}, "signals": {"busy_count": 1, "queued_outbound_count": 2, "inbound_packet_count": 3}},
            ), patch(
                "mystictools.watch.doors_snapshot",
                return_value={"node_temp_count": 4, "dropfile_count": 5, "unreadable_dropfile_count": 0},
            ), patch(
                "mystictools.watch.read_state",
                return_value={"available": True, "qualified": True, "state": {}, "ages": {}, "error": None, "path": "state"},
            ), patch(
                "mystictools.watch.recovery_tree_counts", return_value={"rollback": 1, "failed": 2, "total": 3}
            ):
                snap = watch_snapshot(root)
        self.assertEqual(snap["health"], "ok")
        self.assertEqual(snap["runtime"]["node_processes"], 0)
        self.assertEqual(len(snap["network"]["listeners"]), 2)
        self.assertEqual(snap["recovery_trees"]["total"], 3)
        self.assertEqual(snap["metrics_schema"], 3)
        nodes.assert_called_once_with(root.resolve(), runtime=runtime_value, provider=provider_value)

    def test_render_watch_is_compact_and_privacy_safe(self):
        snapshot = {
            "root": "/srv/mystic",
            "health": "warning",
            "metrics_schema": 3,
            "runtime": {"available": True, "mis_running": True, "node_processes": 1},
            "nodes": {"nodes": [{"node": 2, "pid": 42, "native_qualified": True, "native": {"user": "Sysop", "action": "Main menu"}}]},
            "network": {"available": True, "listeners": [{}]},
            "fidonet": {"poll": {"active": True}, "signals": {"busy_count": 0, "queued_outbound_count": 1, "inbound_packet_count": 0}},
            "doors": {"node_temp_count": 1, "dropfile_count": 2, "unreadable_dropfile_count": 0},
            "recovery": {"available": True, "qualified": True},
            "recovery_trees": {"rollback": 1, "failed": 0, "total": 1},
        }
        text = render_watch(snapshot)
        self.assertIn("health=warning", text)
        self.assertIn("node=2 pid=42 user=Sysop action=Main menu", text)
        self.assertIn("rollback_trees=1", text)
        self.assertNotIn("argv=", text)
        self.assertNotIn("password", text.lower())


if __name__ == "__main__":
    unittest.main()
