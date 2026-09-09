import os
import tempfile
import unittest
from pathlib import Path

from mystictools.network import health_snapshot, network_snapshot


def _write_proc_process(root: Path, pid: int, sockets: dict[str, str]) -> None:
    fd = root / str(pid) / "fd"
    fd.mkdir(parents=True)
    for name, target in sockets.items():
        os.symlink(target, fd / name)


class NetworkTests(unittest.TestCase):
    def test_maps_listener_inode_to_mis_pid(self):
        with tempfile.TemporaryDirectory() as td:
            proc = Path(td)
            (proc / "net").mkdir()
            (proc / "net" / "tcp").write_text(
                "  sl  local_address rem_address   st tx_queue rx_queue tr tm->when retrnsmt   uid  timeout inode\n"
                "   0: 00000000:091A 00000000:0000 0A 00000000:00000000 00:00000000 00000000  1000 0 4242\n",
                encoding="ascii",
            )
            (proc / "net" / "tcp6").write_text(
                "  sl  local_address rem_address   st tx_queue rx_queue tr tm->when retrnsmt   uid  timeout inode\n",
                encoding="ascii",
            )
            _write_proc_process(proc, 101, {"3": "socket:[4242]"})
            processes = {"mis": [{"pid": 101}], "nodes": []}
            result = network_snapshot(processes, proc)
            self.assertTrue(result["available"])
            self.assertEqual(result["listeners"][0]["pid"], 101)
            self.assertEqual(result["listeners"][0]["port"], 2330)
            self.assertEqual(result["listeners"][0]["address"], "0.0.0.0")

    def test_health_warns_when_mis_missing(self):
        runtime = {"mis_running": False, "processes": {"available": True}}
        network = {"available": True, "listeners": []}
        result = health_snapshot(runtime, network)
        self.assertEqual(result["status"], "warning")


if __name__ == "__main__":
    unittest.main()
