import json
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest.mock import patch

from mystictools.exporter import create_server


class ExporterTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = {
            "schema_version": 3,
            "root": "/srv/mystic",
            "health": "ok",
            "values": {"mystictools_runtime_available": 1},
        }
        self.patch = patch("mystictools.exporter.metrics_snapshot", return_value=self.snapshot)
        self.patch.start()
        self.server = create_server(Path("/srv/mystic"), "127.0.0.1", 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        host, port = self.server.server_address
        self.base = f"http://{host}:{port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.patch.stop()

    def test_metrics_endpoint(self):
        with urlopen(self.base + "/metrics", timeout=2) as response:
            body = response.read().decode()
            self.assertEqual(response.status, 200)
            self.assertIn("text/plain", response.headers["Content-Type"])
            self.assertEqual(response.headers["Cache-Control"], "no-store")
            self.assertIn("mystictools_runtime_available 1", body)

    def test_healthz_endpoint(self):
        with urlopen(self.base + "/healthz", timeout=2) as response:
            payload = json.loads(response.read().decode())
            self.assertEqual(response.status, 200)
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["health"], "ok")
            self.assertEqual(payload["metrics_schema_version"], 3)

    def test_unknown_path_is_404(self):
        with self.assertRaises(HTTPError) as caught:
            urlopen(self.base + "/unknown", timeout=2)
        self.assertEqual(caught.exception.code, 404)

    def test_mutating_methods_are_rejected(self):
        request = Request(self.base + "/metrics", data=b"x", method="POST")
        with self.assertRaises(HTTPError) as caught:
            urlopen(request, timeout=2)
        self.assertEqual(caught.exception.code, 405)

    def test_probe_failure_returns_503_without_details(self):
        with patch("mystictools.exporter.metrics_snapshot", side_effect=RuntimeError("secret detail")):
            with self.assertRaises(HTTPError) as caught:
                urlopen(self.base + "/healthz", timeout=2)
            self.assertEqual(caught.exception.code, 503)
            payload = json.loads(caught.exception.read().decode())
            self.assertEqual(payload["error"], "RuntimeError")
            self.assertNotIn("secret detail", json.dumps(payload))


if __name__ == "__main__":
    unittest.main()
