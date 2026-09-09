import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mystictools.metrics import metrics_snapshot, render_prometheus


class MetricsTests(unittest.TestCase):
    def test_metrics_snapshot_shape(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with patch("mystictools.metrics.runtime_snapshot") as runtime, patch(
                "mystictools.metrics.network_snapshot"
            ) as network, patch("mystictools.metrics.operational_checks") as operations:
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
                snap = metrics_snapshot(root)
                self.assertEqual(snap["schema_version"], 1)
                self.assertEqual(snap["values"]["mystic_mis_running"], 1)
                self.assertEqual(snap["values"]["mystic_node_processes"], 2)
                self.assertEqual(snap["values"]["mystic_listeners"], 2)
                self.assertEqual(snap["values"]["mystic_logs_discovered"], 3)

    def test_prometheus_renderer_omits_none_values(self):
        text = render_prometheus(
            {
                "values": {
                    "mystictools_up": 1,
                    "mystic_mis_running": 0,
                    "mystic_node_processes": 0,
                    "mystic_listeners": 0,
                    "mystic_logs_discovered": 0,
                    "mystic_disk_free_bytes": None,
                    "mystic_disk_free_percent": None,
                    "mystic_operational_warnings": 0,
                    "mystic_health_status": 1,
                }
            }
        )
        self.assertIn("mystictools_up 1", text)
        self.assertIn("mystic_health_status 1", text)
        self.assertNotIn("mystic_disk_free_bytes", text)


if __name__ == "__main__":
    unittest.main()
