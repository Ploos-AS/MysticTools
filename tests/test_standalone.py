from __future__ import annotations

import sys
import unittest
from unittest.mock import patch

from mystictools import standalone


class StandaloneTests(unittest.TestCase):
    def test_every_public_name_maps_to_expected_command(self) -> None:
        expected = {
            "mysticstatus": "status",
            "mysticcheck": "check",
            "mysticwho": "who",
            "mysticnodes": "nodes",
            "mysticlog": "logs",
            "mysticnet": "network",
            "mysticfidonet": "fidonet",
            "mysticdoors": "doors",
            "mysticusers": "users",
            "mysticstats": "stats",
            "mystichealth": "health",
            "mysticdoctor": "doctor",
            "mysticbackup": "backup",
            "mysticrestore": "restore",
            "mysticmetrics": "metrics",
        }
        self.assertEqual(standalone.COMMANDS, expected)

    @patch("mystictools.standalone.app_main", return_value=7)
    def test_dispatch_preserves_arguments(self, app_main) -> None:
        with patch.object(sys, "argv", ["mysticnet", "--root", "/srv/mystic", "--json"]):
            self.assertEqual(standalone.main(), 7)
        app_main.assert_called_once_with(["--root", "/srv/mystic", "--json", "network"])

    def test_unknown_entry_point_is_rejected(self) -> None:
        with patch.object(sys, "argv", ["not-a-mystic-tool"]):
            with self.assertRaises(SystemExit):
                standalone.main([])


if __name__ == "__main__":
    unittest.main()
