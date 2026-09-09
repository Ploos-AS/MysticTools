import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mystictools.nodes import nodes_snapshot


class NodeTests(unittest.TestCase):
    def test_nodes_snapshot_preserves_unknown_node(self):
        runtime = {
            "processes": {
                "available": True,
                "source": "procfs",
                "nodes": [
                    {
                        "pid": 123,
                        "node": None,
                        "node_source": None,
                        "started_at": 1000.0,
                        "runtime_seconds": 42,
                        "exe": "/mystic/mystic",
                        "argv": ["/mystic/mystic", "-T"],
                    }
                ],
            }
        }
        with tempfile.TemporaryDirectory() as td:
            with patch("mystictools.nodes.runtime_snapshot", return_value=runtime):
                result = nodes_snapshot(Path(td))
        self.assertTrue(result["ok"])
        self.assertEqual(result["count"], 1)
        self.assertIsNone(result["nodes"][0]["node"])
        self.assertEqual(result["nodes"][0]["runtime_seconds"], 42)
        self.assertEqual(result["nodes"][0]["arguments"], ["-T"])

    def test_nodes_snapshot_exposes_explicit_node(self):
        runtime = {
            "processes": {
                "available": True,
                "source": "procfs",
                "nodes": [
                    {
                        "pid": 456,
                        "node": 3,
                        "node_source": "argv",
                        "started_at": None,
                        "runtime_seconds": None,
                        "exe": "/mystic/mystic",
                        "argv": ["/mystic/mystic", "-N3"],
                    }
                ],
            }
        }
        with tempfile.TemporaryDirectory() as td:
            with patch("mystictools.nodes.runtime_snapshot", return_value=runtime):
                result = nodes_snapshot(Path(td))
        self.assertEqual(result["nodes"][0]["node"], 3)
        self.assertEqual(result["nodes"][0]["node_source"], "argv")


if __name__ == "__main__":
    unittest.main()
