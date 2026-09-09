from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from mystictools.cli import main


class CliRegressionTests(unittest.TestCase):
    def test_nodes_human_output_uses_arguments_model(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            result = {
                "ok": True,
                "available": True,
                "source": "procfs",
                "count": 1,
                "nodes": [
                    {
                        "pid": 123,
                        "node": 2,
                        "node_source": "argv",
                        "started_at": None,
                        "runtime_seconds": 10,
                        "exe": "/mystic/mystic",
                        "arguments": ["-N2"],
                        "native": None,
                        "native_qualified": False,
                    }
                ],
                "native_provider": {"available": False, "qualified": False},
            }
            output = io.StringIO()
            with patch("mystictools.cli.detect_root", return_value=root), patch(
                "mystictools.cli.nodes_snapshot", return_value=result
            ), redirect_stdout(output):
                code = main(["nodes"])
            self.assertEqual(code, 0)
            self.assertIn("node=2 pid=123", output.getvalue())
            self.assertIn("args: -N2", output.getvalue())

    def test_users_human_output_uses_privacy_safe_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            result = {
                "available": True,
                "qualified": True,
                "source": "sidecar-default",
                "path": str(root / "mystictools-users.json"),
                "schema_version": 1,
                "generated_at": 123,
                "count": 1,
                "users": [
                    {
                        "id": 1,
                        "handle": "Sysop",
                        "security_level": 255,
                        "calls": 42,
                        "uploads": None,
                        "downloads": None,
                        "posts": None,
                        "last_on": 123,
                    }
                ],
                "error": None,
            }
            output = io.StringIO()
            with patch("mystictools.cli.detect_root", return_value=root), patch(
                "mystictools.cli.users_snapshot", return_value=result
            ), redirect_stdout(output):
                code = main(["users"])
            self.assertEqual(code, 0)
            self.assertIn("id=1 handle=Sysop level=255 calls=42", output.getvalue())

    def test_metrics_prometheus_uses_runtime_available_contract(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            snapshot = {
                "schema_version": 2,
                "root": str(root),
                "health": "ok",
                "values": {"mystictools_runtime_available": 1},
            }
            output = io.StringIO()
            with patch("mystictools.cli.detect_root", return_value=root), patch(
                "mystictools.cli.metrics_snapshot", return_value=snapshot
            ), patch("mystictools.cli.render_prometheus", return_value="mystictools_runtime_available 1\n"), redirect_stdout(output):
                code = main(["metrics", "--prometheus"])
            self.assertEqual(code, 0)
            self.assertIn("mystictools_runtime_available 1", output.getvalue())

    def test_json_and_prometheus_are_mutually_exclusive(self) -> None:
        with self.assertRaises(SystemExit) as raised:
            main(["--json", "metrics", "--prometheus"])
        self.assertEqual(raised.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
