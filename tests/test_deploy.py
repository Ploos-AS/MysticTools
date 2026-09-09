import unittest
from pathlib import Path


class DeploymentTests(unittest.TestCase):
    def test_systemd_unit_is_loopback_and_hardened(self):
        text = Path("deploy/systemd/mystictools-exporter.service").read_text(encoding="utf-8")
        self.assertIn("--bind 127.0.0.1", text)
        self.assertIn("NoNewPrivileges=true", text)
        self.assertIn("ProtectSystem=strict", text)
        self.assertIn("ReadOnlyPaths=/opt/mystic", text)

    def test_compose_preserves_host_proc_visibility_and_loopback_publish(self):
        text = Path("compose.exporter.yaml").read_text(encoding="utf-8")
        self.assertIn("pid: host", text)
        self.assertIn("read_only: true", text)
        self.assertIn("no-new-privileges:true", text)
        self.assertIn("cap_drop:", text)
        self.assertIn("127.0.0.1:9108:9108", text)
        self.assertIn(":/mystic:ro", text)

    def test_prometheus_example_scrapes_exporter(self):
        text = Path("deploy/prometheus/prometheus.yml").read_text(encoding="utf-8")
        self.assertIn("job_name: mystictools", text)
        self.assertIn("127.0.0.1:9108", text)


if __name__ == "__main__":
    unittest.main()
