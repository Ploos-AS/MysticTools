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

    def test_fragment_directory_is_aggregated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fragment_dir = root / "mystictools-nodes.d"
            fragment_dir.mkdir()
            for node in (2, 1):
                (fragment_dir / f"node-{node}.json").write_text(
                    json.dumps(
                        {
                            "schema_version": 1,
                            "generated_at": 1000,
                            "nodes": [
                                {
                                    "node": node,
                                    "user": f"User{node}",
                                    "action": None,
                                    "server": "TELNET",
                                    "invisible": False,
                                    "available_for_messages": True,
                                }
                            ],
                        }
                    )
                )
            snap = load_node_snapshot(root, now=1010)
            self.assertTrue(snap["qualified"])
            self.assertEqual(snap["source"], "fragment-default")
            self.assertEqual([item["node"] for item in snap["nodes"]], [1, 2])
            self.assertEqual(snap["fresh_fragment_count"], 2)
            self.assertEqual(snap["stale_fragment_count"], 0)

    def test_stale_fragment_is_excluded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fragment_dir = root / "mystictools-nodes.d"
            fragment_dir.mkdir()
            (fragment_dir / "node-1.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "generated_at": 100,
                        "nodes": [{"node": 1}],
                    }
                )
            )
            snap = load_node_snapshot(root, now=1000)
            self.assertFalse(snap["qualified"])
            self.assertEqual(snap["nodes"], [])
            self.assertEqual(snap["stale_fragment_count"], 1)

    def test_invalid_fragment_marks_provider_unqualified(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fragment_dir = root / "mystictools-nodes.d"
            fragment_dir.mkdir()
            (fragment_dir / "node-1.json").write_text(json.dumps({"schema_version": 99, "nodes": []}))
            snap = load_node_snapshot(root, now=1000)
            self.assertFalse(snap["qualified"])
            self.assertIn("schema", snap["error"])

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
        self.assertTrue(merged[0]["native_active"])
        self.assertEqual(merged[0]["native_correlation"], "explicit-node-match")

    def test_unmatched_native_node_is_inactive_when_all_process_nodes_are_explicit(self) -> None:
        processes = [
            {
                "pid": 123,
                "node": 1,
                "node_source": "argv",
                "started_at": None,
                "runtime_seconds": None,
                "exe": "/mystic/mystic",
                "arguments": ["-N1"],
            }
        ]
        provider = {"qualified": True, "nodes": [{"node": 2, "user": "OldUser"}]}
        merged = merge_native_nodes(processes, provider)
        native_only = next(item for item in merged if item["node"] == 2)
        self.assertFalse(native_only["native_active"])
        self.assertEqual(native_only["native_correlation"], "no-matching-process")

    def test_unmatched_native_node_is_unresolved_with_auto_selected_process(self) -> None:
        processes = [
            {
                "pid": 123,
                "node": None,
                "node_source": None,
                "started_at": None,
                "runtime_seconds": None,
                "exe": "/mystic/mystic",
                "arguments": [],
            }
        ]
        provider = {"qualified": True, "nodes": [{"node": 2, "user": "PossibleUser"}]}
        merged = merge_native_nodes(processes, provider)
        native_only = next(item for item in merged if item["node"] == 2)
        self.assertIsNone(native_only["native_active"])
        self.assertEqual(native_only["native_correlation"], "unresolved-auto-selected-process")


if __name__ == "__main__":
    unittest.main()
