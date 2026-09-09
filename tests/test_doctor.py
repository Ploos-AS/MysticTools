import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mystictools.doctor import doctor_snapshot


class DoctorTests(unittest.TestCase):
    def test_warning_summary_across_sources(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with patch("mystictools.doctor.runtime_snapshot") as runtime, patch(
                "mystictools.doctor.network_snapshot"
            ) as network, patch("mystictools.doctor.operational_checks") as operations, patch(
                "mystictools.doctor.load_node_snapshot"
            ) as node_provider, patch("mystictools.doctor.users_snapshot") as users, patch(
                "mystictools.doctor.fidonet_snapshot"
            ) as fidonet, patch("mystictools.doctor.doors_snapshot") as doors:
                runtime.return_value = {"processes": {"available": True}, "mis_running": False}
                network.return_value = {"available": True, "listeners": []}
                operations.return_value = {"warning_count": 1}
                node_provider.return_value = {"available": True, "qualified": True, "stale_fragment_count": 2}
                users.return_value = {"available": True, "qualified": True, "count": 10}
                fidonet.return_value = {"qualified_config": False, "signals": {"busy_count": 1}}
                doors.return_value = {"unreadable_dropfile_count": 0}
                snap = doctor_snapshot(root)
                self.assertEqual(snap["status"], "warning")
                self.assertGreater(snap["counts"]["warning"], 0)
                self.assertTrue(any(item["name"] == "node_provider" for item in snap["findings"]))

    def test_unavailable_runtime_is_explicit(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with patch("mystictools.doctor.runtime_snapshot") as runtime, patch(
                "mystictools.doctor.network_snapshot"
            ) as network, patch("mystictools.doctor.operational_checks") as operations, patch(
                "mystictools.doctor.load_node_snapshot"
            ) as node_provider, patch("mystictools.doctor.users_snapshot") as users, patch(
                "mystictools.doctor.fidonet_snapshot"
            ) as fidonet, patch("mystictools.doctor.doors_snapshot") as doors:
                runtime.return_value = {"processes": {"available": False}, "mis_running": False}
                network.return_value = {"available": False, "listeners": []}
                operations.return_value = {"warning_count": 0}
                node_provider.return_value = {"available": False, "qualified": False}
                users.return_value = {"available": False, "qualified": False}
                fidonet.return_value = {"qualified_config": True, "signals": {"busy_count": 0}}
                doors.return_value = {"unreadable_dropfile_count": 0}
                snap = doctor_snapshot(root)
                self.assertEqual(snap["status"], "unavailable")
                self.assertEqual(snap["counts"]["unavailable"], 2)

    def test_critical_finding_outranks_unavailable_probe(self):
        root = Path("/srv/mystic")
        snap = doctor_snapshot(
            root,
            runtime={"processes": {"available": False}, "mis_running": False},
            network={"available": False, "listeners": []},
            operations={"warning_count": 0, "checks": [{"name": "disk", "status": "critical", "detail": "full"}]},
            node_provider={"available": False, "qualified": False},
            users={"available": False, "qualified": False},
            fidonet={"qualified_config": True, "signals": {"busy_count": 0}},
            doors={"unreadable_dropfile_count": 0},
        )
        self.assertEqual(snap["status"], "critical")
        self.assertEqual(snap["counts"]["critical"], 1)
        self.assertEqual(snap["counts"]["unavailable"], 2)


if __name__ == "__main__":
    unittest.main()
