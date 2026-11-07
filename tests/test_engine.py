import sys
import types
import unittest
from unittest.mock import patch

try:
    from macroflow.engine import Runner
except ImportError:
    Runner = None


@unittest.skipIf(Runner is None, "PySide6 is not available in this environment")
class EngineTests(unittest.TestCase):
    def test_count_repeat(self):
        clicks = []
        fake = types.SimpleNamespace(FAILSAFE=True, click=lambda x, y: clicks.append((x, y)))
        step = {"action": "click", "enabled": True, "delay_ms": 0,
                "region": {"x": 10, "y": 10, "w": 20, "h": 20}}
        runner = Runner([step], repeat_mode="count", repeat_count=3)
        completed = []
        runner.cycle_changed.connect(lambda done, total: completed.append((done, total)))
        with patch.dict(sys.modules, {"pyautogui": fake}):
            runner.run()
        self.assertEqual(clicks, [(20, 20)] * 3)
        self.assertEqual(completed[-1], (3, 3))

    def test_forever_stops(self):
        fake = types.SimpleNamespace(FAILSAFE=True)
        runner = Runner([{"action": "wait", "enabled": True, "delay_ms": 0}], repeat_mode="forever")
        cycles = []
        def record(done, total):
            cycles.append(done)
            if done == 2:
                runner.stop()
        runner.cycle_changed.connect(record)
        with patch.dict(sys.modules, {"pyautogui": fake}):
            runner.run()
        self.assertEqual(cycles, [1, 2])

    def test_empty_scenario_does_not_loop(self):
        fake = types.SimpleNamespace(FAILSAFE=True)
        runner = Runner([{"action": "wait", "enabled": False}], repeat_mode="forever")
        messages = []
        runner.ended.connect(messages.append)
        with patch.dict(sys.modules, {"pyautogui": fake}):
            runner.run()
        self.assertEqual(len(messages), 1)
        self.assertIn("Нет включённых", messages[0])


if __name__ == "__main__":
    unittest.main()
