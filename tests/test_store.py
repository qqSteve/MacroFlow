import os
import tempfile
import unittest
from unittest.mock import patch

from macroflow.store import fresh_script, fresh_step, load_scripts, save_scripts


class StoreTests(unittest.TestCase):
    def test_roundtrip(self):
        with tempfile.TemporaryDirectory() as temporary:
            with patch.dict(os.environ, {"APPDATA": temporary}):
                script = fresh_script("Документы 1С")
                script["steps"].append(fresh_step())
                save_scripts([script])
                reloaded = load_scripts()
                self.assertEqual(reloaded[0]["name"], "Документы 1С")
                self.assertEqual(reloaded[0]["steps"][0]["action"], "click")

    def test_empty(self):
        with tempfile.TemporaryDirectory() as temporary:
            with patch.dict(os.environ, {"APPDATA": temporary}):
                self.assertEqual(load_scripts(), [])


if __name__ == "__main__":
    unittest.main()
