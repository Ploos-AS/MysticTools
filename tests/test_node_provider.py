from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from mystictools.node_provider import load_node_snapshot, merge_native_nodes


class NodeProviderTests(unittest.TestCase):
    def test_valid_sidecar_is_qualified(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "mystictools-nodes.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "nodes": [
                            {
                                "node": 2,
                                "user": "Sysop",
                                "action": "Reading messages",
                                "server": "Telnet",
                                "invisible": False,
                                "available_for_messages": True,
                            }
                        ],
                    }
                )
            )
            snap = load_node_snapshot(root)
            self.assertTrue(snap["qualified"])
            self.assertEqual(snap["nodes"][0]["node"], 2)

    def test_invalid_schema_is_not_qualified(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "mystictools-nodes.json").write_text(json.dumps({"schema_version": 99, "nodes": []}))
            snap = load_node_snapshot(root)
            self.assertFalse(snap["qualified"])
            self.assertIn("schema", snap["error"])

    def test_merge_preserves_procfs_and_enriches_matching_node(self) -> None:
        processes = [
            {
                "pid": 123,
                "node": 2,
                "node_source": "argv",
                "started_at": 10.0,
                "runtime_seconds": 20,
                "exe": "/mystic/mystic",
                "arguments": ["-N2"],
            }
        ]
        provider = {
            "qualified": True,
            "nodes": [{"node": 2, "user": "Sysop", "action": "Main menu", "server": "Telnet", "invisible": False, "available_for_messages": True}],
        }
        merged = merge_native_nodes(processes, provider)
        self.assertEqual(merged[0]["pid"], 123)
        self.assertEqual(merged[0]["native"]["user"], "Sysop")
        self.assertTrue(merged[0]["native_qualified"])


if __name__ == "__main__":
    unittest.main()
