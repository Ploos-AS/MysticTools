import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mystictools.stats import stats_snapshot


class StatsTests(unittest.TestCase):
    def test_stats_aggregates_qualified_user_totals(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with patch("mystictools.stats.users_snapshot") as users, patch(
                "mystictools.stats.runtime_snapshot"
            ) as runtime, patch("mystictools.stats.network_snapshot") as network, patch(
                "mystictools.stats.fidonet_snapshot"
            ) as fidonet, patch("mystictools.stats.doors_snapshot") as doors:
                users.return_value = {
                    "qualified": True,
                    "fresh": True,
                    "complete_scan": True,
                    "count": 2,
                    "users": [
                        {"calls": 10, "uploads": 2, "downloads": 3, "posts": 4},
                        {"calls": 20, "uploads": 5, "downloads": 7, "posts": 11},
                    ],
                }
                runtime.return_value = {
                    "processes": {"available": True, "nodes": [], "mis": []},
                    "mis_running": True,
                    "active_process_count": 2,
                }
                network.return_value = {"available": True, "listeners": [{}, {}]}
                fidonet.return_value = {
                    "qualified_config": True,
                    "signals": {"busy_count": 1, "queued_outbound_count": 2, "inbound_packet_count": 3},
                    "poll": {"active": True},
                }
                doors.return_value = {"node_temp_count": 2, "dropfile_count": 4, "unreadable_dropfile_count": 0}

                snap = stats_snapshot(root)

        self.assertEqual(snap["users"]["users"], 2)
        self.assertEqual(snap["users"]["calls"], 30)
        self.assertEqual(snap["users"]["uploads"], 7)
        self.assertEqual(snap["users"]["downloads"], 10)
        self.assertEqual(snap["users"]["posts"], 15)
        self.assertEqual(snap["runtime"]["node_processes"], 2)
        self.assertEqual(snap["runtime"]["listeners"], 2)

    def test_unqualified_users_do_not_emit_false_totals(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with patch("mystictools.stats.users_snapshot", return_value={"qualified": False, "fresh": False, "complete_scan": False, "count": 0, "users": []}), patch(
                "mystictools.stats.runtime_snapshot",
                return_value={"processes": {"available": False, "nodes": [], "mis": []}, "mis_running": False, "active_process_count": 0},
            ), patch("mystictools.stats.network_snapshot", return_value={"available": False, "listeners": []}), patch(
                "mystictools.stats.fidonet_snapshot",
                return_value={
                    "qualified_config": False,
                    "signals": {"busy_count": 0, "queued_outbound_count": 0, "inbound_packet_count": 0},
                    "poll": {"active": False},
                },
            ), patch(
                "mystictools.stats.doors_snapshot",
                return_value={"node_temp_count": 0, "dropfile_count": 0, "unreadable_dropfile_count": 0},
            ):
                snap = stats_snapshot(root)

        self.assertIsNone(snap["users"]["users"])
        self.assertIsNone(snap["users"]["calls"])
        self.assertIsNone(snap["runtime"]["node_processes"])
        self.assertIsNone(snap["runtime"]["listeners"])

    def test_partial_numeric_user_data_is_not_summed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with patch("mystictools.stats.users_snapshot", return_value={
                "qualified": True,
                "fresh": True,
                "complete_scan": True,
                "count": 2,
                "users": [{"calls": 10, "uploads": 2, "downloads": 3, "posts": 4}, {"calls": None, "uploads": 5, "downloads": 7, "posts": 11}],
            }), patch("mystictools.stats.runtime_snapshot", return_value={"processes": {"available": True, "nodes": [], "mis": []}, "mis_running": False, "active_process_count": 0}), patch("mystictools.stats.network_snapshot", return_value={"available": True, "listeners": []}), patch("mystictools.stats.fidonet_snapshot", return_value={"qualified_config": True, "signals": {"busy_count": 0, "queued_outbound_count": 0, "inbound_packet_count": 0}, "poll": {"active": False}}), patch("mystictools.stats.doors_snapshot", return_value={"node_temp_count": 0, "dropfile_count": 0, "unreadable_dropfile_count": 0}):
                snap = stats_snapshot(root)
        self.assertIsNone(snap["users"]["calls"])
        self.assertEqual(snap["users"]["uploads"], 7)


if __name__ == "__main__":
    unittest.main()
