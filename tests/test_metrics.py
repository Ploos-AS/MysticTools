import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mystictools.metrics import metrics_snapshot, render_prometheus
from mystictools.recovery_state import record_event


class MetricsTests(unittest.TestCase):
    def test_metrics_snapshot_shape(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with patch("mystictools.metrics.runtime_snapshot") as runtime, patch(
                "mystictools.metrics.network_snapshot"
            ) as network, patch("mystictools.metrics.operational_checks") as operations, patch(
                "mystictools.metrics.load_node_snapshot"
            ) as provider, patch("mystictools.metrics.fidonet_snapshot") as fidonet, patch(
                "mystictools.metrics.doors_snapshot"
            ) as doors:
                runtime.return_value = {
                    "processes": {"available": True, "mis": [], "nodes": []},
                    "mis_running": True,
                    "active_process_count": 2,
                }
                network.return_value = {"available": True, "listeners": [{}, {}]}
                operations.return_value = {
                    "logs": {"count": 3},
                    "disk": {"available": True, "free_bytes": 1024, "free_percent": 50.0},
                    "warning_count": 1,
                }
                provider.return_value = {"available": True, "qualified": True}
                fidonet.return_value = {
                    "qualified_config": True,
                    "signals": {
                        "busy_count": 1,
                        "queued_outbound_count": 4,
                        "inbound_packet_count": 2,
                    },
                    "poll": {"active": True},
                }
                doors.return_value = {
                    "node_temp_count": 5,
                    "dropfile_count": 6,
                    "unreadable_dropfile_count": 1,
                }
                snap = metrics_snapshot(root)
                self.assertEqual(snap["schema_version"], 3)
                self.assertEqual(snap["values"]["mystictools_mis_running"], 1)
                self.assertEqual(snap["values"]["mystictools_node_processes"], 2)
                self.assertEqual(snap["values"]["mystictools_listener_count"], 2)
                self.assertEqual(snap["values"]["mystictools_logs_discovered"], 3)
                self.assertEqual(snap["values"]["mystictools_fidonet_outbound_queue_candidates"], 4)
                self.assertEqual(snap["values"]["mystictools_door_dropfiles"], 6)
                self.assertEqual(snap["values"]["mystictools_recovery_state_available"], 0)

    def test_unavailable_runtime_does_not_invent_runtime_values(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with patch("mystictools.metrics.runtime_snapshot") as runtime, patch(
                "mystictools.metrics.network_snapshot"
            ) as network, patch("mystictools.metrics.operational_checks") as operations, patch(
                "mystictools.metrics.load_node_snapshot"
            ) as provider, patch("mystictools.metrics.fidonet_snapshot") as fidonet, patch(
                "mystictools.metrics.doors_snapshot"
            ) as doors:
                runtime.return_value = {
                    "processes": {"available": False, "mis": [], "nodes": []},
                    "mis_running": False,
                    "active_process_count": 0,
                }
                network.return_value = {"available": False, "listeners": []}
                operations.return_value = {
                    "logs": {"count": 0},
                    "disk": {"available": False, "free_bytes": None, "free_percent": None},
                    "warning_count": 0,
                }
                provider.return_value = {"available": False, "qualified": False}
                fidonet.return_value = {
                    "qualified_config": False,
                    "signals": {"busy_count": 0, "queued_outbound_count": 0, "inbound_packet_count": 0},
                    "poll": {"active": False},
                }
                doors.return_value = {"node_temp_count": 0, "dropfile_count": 0, "unreadable_dropfile_count": 0}
                snap = metrics_snapshot(root)
                self.assertEqual(snap["values"]["mystictools_runtime_available"], 0)
                self.assertIsNone(snap["values"]["mystictools_mis_running"])
                self.assertIsNone(snap["values"]["mystictools_node_processes"])
                self.assertIsNone(snap["values"]["mystictools_listener_count"])
                self.assertIsNone(snap["values"]["mystictools_fidonet_poll_active"])

    def test_recovery_event_metrics(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "mystic"
            root.mkdir()
            record_event(root, "backup", True)
            with patch("mystictools.metrics.runtime_snapshot") as runtime, patch(
                "mystictools.metrics.network_snapshot"
            ) as network, patch("mystictools.metrics.operational_checks") as operations, patch(
                "mystictools.metrics.load_node_snapshot"
            ) as provider, patch("mystictools.metrics.fidonet_snapshot") as fidonet, patch(
                "mystictools.metrics.doors_snapshot"
            ) as doors:
                runtime.return_value = {"processes": {"available": False, "mis": [], "nodes": []}, "mis_running": False, "active_process_count": 0}
                network.return_value = {"available": False, "listeners": []}
                operations.return_value = {"logs": {"count": 0}, "disk": {"available": False, "free_bytes": None, "free_percent": None}, "warning_count": 0}
                provider.return_value = {"available": False, "qualified": False}
                fidonet.return_value = {"qualified_config": False, "signals": {"busy_count": 0, "queued_outbound_count": 0, "inbound_packet_count": 0}, "poll": {"active": False}}
                doors.return_value = {"node_temp_count": 0, "dropfile_count": 0, "unreadable_dropfile_count": 0}
                snap = metrics_snapshot(root)
            self.assertEqual(snap["values"]["mystictools_recovery_state_qualified"], 1)
            self.assertEqual(snap["values"]["mystictools_last_backup_success"], 1)
            self.assertIsNotNone(snap["values"]["mystictools_last_backup_age_seconds"])

    def test_prometheus_renderer_uses_one_namespace_and_omits_none_values(self):
        text = render_prometheus(
            {
                "values": {
                    "mystictools_runtime_available": 1,
                    "mystictools_mis_running": 0,
                    "mystictools_listener_count": None,
                    "mystictools_health_status": 1,
                }
            }
        )
        self.assertIn("mystictools_runtime_available 1", text)
        self.assertIn("mystictools_health_status 1", text)
        self.assertNotIn("mystictools_listener_count", text)
        for line in text.splitlines():
            if line.startswith(("# HELP ", "# TYPE ", "mystictools_")):
                self.assertNotIn(" mystic_", line)


if __name__ == "__main__":
    unittest.main()
