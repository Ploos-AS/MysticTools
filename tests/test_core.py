import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mystictools.core import check_installation, detect_root


class CoreTests(unittest.TestCase):
    def test_explicit_root_wins(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(detect_root(td), Path(td).resolve())

    def test_env_root(self):
        with tempfile.TemporaryDirectory() as td:
            with patch.dict(os.environ, {"MYSTIC_ROOT": td}, clear=False):
                self.assertEqual(detect_root(), Path(td).resolve())

    def test_check_reports_missing_paths(self):
        with tempfile.TemporaryDirectory() as td:
            result = check_installation(Path(td))
            self.assertFalse(result["ok"])
            self.assertGreater(result["warning_count"], 0)


if __name__ == "__main__":
    unittest.main()
