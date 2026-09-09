from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

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

    def test_missing_paths_are_reported_without_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            snap = fidonet_snapshot(Path(tmp))
            self.assertFalse(snap["paths"]["echomail_root"]["exists"])
            self.assertEqual(snap["signals"]["busy_count"], 0)
            self.assertEqual(snap["signals"]["queued_outbound_count"], 0)


if __name__ == "__main__":
    unittest.main()
