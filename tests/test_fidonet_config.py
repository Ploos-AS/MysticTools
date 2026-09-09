from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mystictools.fidonet import fidonet_snapshot
from mystictools.fidonet_config import fidonet_config


class FidoNetConfigTests(unittest.TestCase):
    def test_defaults_are_explicitly_unqualified(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {}, clear=True):
            root = Path(tmp)
            config = fidonet_config(root)
            self.assertFalse(config["qualified_config"])
            self.assertEqual(config["paths"]["inbound"]["source"], "mystic-default")

    def test_ini_can_qualify_all_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {}, clear=True):
            root = Path(tmp)
            (root / "mystictools-fidonet.ini").write_text(
                "[paths]\n"
                "inbound = fido/in\n"
                "inbound_unsecured = fido/in/unsecure\n"
                "outbound_primary = fido/out/primary\n"
                "semaphore = fido/semaphore\n",
                encoding="utf-8",
            )
            config = fidonet_config(root)
            self.assertTrue(config["qualified_config"])
            self.assertEqual(config["paths"]["inbound"]["source"], "mystictools-ini")
            self.assertEqual(config["paths"]["inbound"]["path"], str(root / "fido" / "in"))

    def test_environment_wins_over_ini(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "mystictools-fidonet.ini").write_text(
                "[paths]\ninbound = ini/in\n",
                encoding="utf-8",
            )
            with patch.dict(os.environ, {"MYSTICTOOLS_FIDONET_INBOUND": "/override/in"}, clear=True):
                config = fidonet_config(root)
            self.assertEqual(config["paths"]["inbound"]["path"], "/override/in")
            self.assertEqual(config["paths"]["inbound"]["source"], "environment")

    def test_poll_context_detects_mis_poll_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {}, clear=True):
            processes = {
                "mis": [
                    {"pid": 10, "argv": ["/mystic/mis", "server"], "exe": "/mystic/mis"},
                    {"pid": 11, "argv": ["/mystic/mis", "POLL", "21:1/100"], "exe": "/mystic/mis"},
                ]
            }
            snap = fidonet_snapshot(Path(tmp), processes=processes)
            self.assertTrue(snap["poll"]["active"])
            self.assertEqual(snap["poll"]["count"], 1)
            self.assertEqual(snap["poll"]["processes"][0]["pid"], 11)


if __name__ == "__main__":
    unittest.main()
