from __future__ import annotations

import sys
import unittest
from unittest.mock import patch

from mystictools import cli, standalone


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
    def test_dispatch_places_global_arguments_before_command(self, app_main) -> None:
        with patch.object(sys, "argv", ["mysticnet", "--root", "/srv/mystic", "--json"]):
            self.assertEqual(standalone.main(), 7)
        app_main.assert_called_once_with(["--root", "/srv/mystic", "--json", "network"])

    @patch("mystictools.standalone.app_main", return_value=7)
    def test_dispatch_places_subcommand_arguments_after_command(self, app_main) -> None:
        with patch.object(
            sys,
            "argv",
            ["mysticlog", "--root=/srv/mystic", "--json", "mis", "--tail", "25", "--contains", "error"],
        ):
            self.assertEqual(standalone.main(), 7)
        app_main.assert_called_once_with(
            ["--root=/srv/mystic", "--json", "logs", "mis", "--tail", "25", "--contains", "error"]
        )

    def test_all_standalone_routes_parse_with_real_umbrella_parser(self) -> None:
        parser = cli.build_parser()
        samples = {
            "status": [],
            "check": [],
            "who": [],
            "nodes": [],
            "logs": ["mis", "--tail", "5"],
            "network": [],
            "fidonet": [],
            "doors": [],
            "users": [],
            "stats": [],
            "health": [],
            "doctor": [],
            "backup": ["/tmp/mystic-backup.tar.gz", "--allow-unverified"],
            "restore": ["/tmp/mystic-backup.tar.gz", "--execute", "--replace-existing"],
            "metrics": ["--prometheus"],
        }
        for command in standalone.COMMANDS.values():
            with self.subTest(command=command):
                argv = standalone._dispatch_argv(
                    command,
                    ["--root", "/srv/mystic", *samples[command]],
                )
                parsed = parser.parse_args(argv)
                self.assertEqual(parsed.command, command)
                self.assertEqual(parsed.root, "/srv/mystic")

    def test_metrics_prometheus_stays_after_subcommand(self) -> None:
        argv = standalone._dispatch_argv("metrics", ["--root", "/srv/mystic", "--prometheus"])
        self.assertEqual(argv, ["--root", "/srv/mystic", "metrics", "--prometheus"])
        parsed = cli.build_parser().parse_args(argv)
        self.assertTrue(parsed.prometheus)

    def test_unknown_entry_point_is_rejected(self) -> None:
        with patch.object(sys, "argv", ["not-a-mystic-tool"]):
            with self.assertRaises(SystemExit):
                standalone.main([])


if __name__ == "__main__":
    unittest.main()
