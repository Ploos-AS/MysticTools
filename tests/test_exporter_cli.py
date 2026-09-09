import unittest
from pathlib import Path
from unittest.mock import patch

from mystictools import app
from mystictools.exporter_cli import main


class ExporterCliTests(unittest.TestCase):
    def test_standalone_cli_invokes_server(self):
        with patch("mystictools.exporter_cli.detect_root", return_value=Path("/srv/mystic")), patch(
            "mystictools.exporter_cli.serve"
        ) as serve:
            code = main(["--root", "/srv/mystic", "--bind", "127.0.0.1", "--port", "9108"])
        self.assertEqual(code, 0)
        serve.assert_called_once_with(Path("/srv/mystic"), "127.0.0.1", 9108)

    def test_umbrella_routes_exporter(self):
        with patch("mystictools.app.exporter_main", return_value=0) as exporter:
            code = app.main(["--root", "/srv/mystic", "exporter", "--port", "9200"])
        self.assertEqual(code, 0)
        exporter.assert_called_once_with(["--root", "/srv/mystic", "--port", "9200"])

    def test_invalid_port_is_rejected(self):
        with self.assertRaises(SystemExit):
            main(["--root", "/srv/mystic", "--port", "0"])


if __name__ == "__main__":
    unittest.main()
