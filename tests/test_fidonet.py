from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mystictools.fidonet import fidonet_snapshot


class FidoNetTests(unittest.TestCase):
    def test_discovers_default_paths_and_signals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "echomail" / "in" / "unsecure").mkdir(parents=True)
            (root / "echomail" / "out" / "primary").mkdir(parents=True)
            (root / "semaphore").mkdir()

            (root / "semaphore" / "echomail.out").write_text("")
            (root / "echomail" / "out" / "primary" / "00010002.bsy").write_text("")
            (root / "echomail" / "out" / "primary" / "00010002.flo").write_text("mail.pkt\n")
            (root / "echomail" / "in" / "mail.pkt").write_bytes(b"packet")

            snap = fidonet_snapshot(root)

            self.assertTrue(snap["paths"]["inbound"]["exists"])
            self.assertTrue(snap["signals"]["echomail_out"])
            self.assertEqual(snap["signals"]["busy_count"], 1)
            self.assertEqual(snap["signals"]["queued_outbound_count"], 1)
            self.assertEqual(snap["signals"]["inbound_packet_count"], 1)
            self.assertFalse(snap["qualified_config"])
            self.assertTrue(snap["qualified_scan"])

    def test_missing_paths_are_reported_without_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            snap = fidonet_snapshot(Path(tmp))
            self.assertFalse(snap["paths"]["echomail_root"]["exists"])
            self.assertEqual(snap["signals"]["busy_count"], 0)
            self.assertEqual(snap["signals"]["queued_outbound_count"], 0)
            self.assertTrue(snap["qualified_scan"])

    def test_scan_error_is_explicitly_degraded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch(
            "mystictools.fidonet._scan_files",
            return_value=([], ["unable to scan test path: permission denied"]),
        ):
            snap = fidonet_snapshot(Path(tmp))
            self.assertFalse(snap["qualified_scan"])
            self.assertTrue(snap["scan_errors"])
            self.assertIn("permission denied", " ".join(snap["scan_errors"]))


if __name__ == "__main__":
    unittest.main()
