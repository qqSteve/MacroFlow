import json
import tempfile
import unittest
from pathlib import Path
from macroflow.exchange import dumps, parse_file, write_file
from macroflow.store import fresh_script, fresh_step
from macroflow.templates import TEMPLATES, build_template


class ExchangeTests(unittest.TestCase):
    def test_roundtrip_and_reassign_ids(self):
        scenario = fresh_script("Обработка документа")
        scenario.update(repeat_mode="count", repeat_count=27, cycle_delay_ms=75)
        scenario["steps"] = [fresh_step("wait")]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "example.mflow"
            write_file(path, [scenario])
            imported = parse_file(path)
        self.assertEqual(imported[0]["repeat_mode"], "count")
        self.assertEqual(imported[0]["repeat_count"], 27)
        self.assertEqual(imported[0]["cycle_delay_ms"], 75)
        self.assertNotEqual(imported[0]["id"], scenario["id"])
        self.assertNotEqual(imported[0]["steps"][0]["id"], scenario["steps"][0]["id"])

    def test_legacy_script(self):
        old = {"id": "old", "name": "Вчерашний", "steps": [{"id": "1", "action": "wait"}]}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "old.json"
            path.write_text(json.dumps([old]), encoding="utf-8")
            imported = parse_file(path)
        self.assertEqual(imported[0]["repeat_mode"], "once")
        self.assertEqual(imported[0]["repeat_count"], 1)

    def test_reject_unknown_and_invalid(self):
        bad = fresh_script("Из интернета")
        bad["steps"] = [{"action": "shell", "delay_ms": 0}]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.mflow"
            path.write_text(dumps([bad]), encoding="utf-8")
            with self.assertRaises(ValueError):
                parse_file(path)

    def test_reject_oversized(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "huge.mflow"
            path.write_bytes(b"x" * (2 * 1024 * 1024 + 1))
            with self.assertRaises(ValueError):
                parse_file(path)

    def test_templates_disabled(self):
        for name in TEMPLATES:
            scenario = build_template(name)
            self.assertGreater(len(scenario["steps"]), 0)
            self.assertTrue(all(not item["enabled"] for item in scenario["steps"]))


if __name__ == "__main__":
    unittest.main()
