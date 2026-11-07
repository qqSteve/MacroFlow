"""Automated GUI checks, run by GitHub Actions with QT_QPA_PLATFORM=offscreen."""
import os
import unittest
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication, QFrame
    from macroflow.app import MainWindow
    from macroflow.visual import SHAPES, vector_icon
except ImportError:
    QApplication = None


@unittest.skipIf(QApplication is None, 'PySide6 unavailable here')
class UiSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def window(self):
        mocks = [
            patch('macroflow.app.load_scripts', return_value=[]),
            patch('macroflow.app.save_scripts'),
            patch('macroflow.app.Recorder.start_listeners', return_value=True),
        ]
        for mock in mocks:
            mock.start()
            self.addCleanup(mock.stop)
        w = MainWindow()
        self.addCleanup(w.close)
        return w

    def test_frameless_shell_icons_and_pages(self):
        w = self.window()
        self.assertTrue(w.windowFlags() & Qt.FramelessWindowHint)
        self.assertEqual(w.pages.count(), 5)
        self.assertEqual(len(w.nav_buttons), 5)
        for idx in range(5):
            w.show_page(idx)
            self.assertTrue(w.nav_buttons[idx].isChecked())
        self.assertFalse(vector_icon('save').isNull())
        self.assertFalse(vector_icon('play').isNull())
        self.assertGreater(len(SHAPES), 30)

    def test_action_editor_and_timing_controls(self):
        w = self.window()
        from macroflow.store import fresh_script
        w.add_new_script(fresh_script('GUI smoke test'))
        w.add_specific_step('click')
        self.assertEqual(w.step_list.count(), 1)
        self.assertEqual(w.step_count.text(), '1')
        self.assertEqual(w.current_step()['action'], 'click')
        w.set_delay_preset(600)
        self.assertEqual(w.current_step()['delay_ms'], 600)
        w.change_step_display(True)
        self.assertTrue(w.steps_compact)
        w.duplicate_step()
        self.assertEqual(w.step_list.count(), 2)
        w.shift_step(-1)
        w.undo_change()
        self.assertIsNotNone(w.current_script())

    def test_recording_and_update_pages_share_shell(self):
        w = self.window()
        self.assertTrue(w.pages.widget(2).findChildren(QFrame, 'workPanel'))
        self.assertTrue(w.pages.widget(3).findChildren(QFrame, 'workPanel'))
        self.assertTrue(w.pages.widget(4).findChildren(QFrame, 'workPanel'))


if __name__ == '__main__':
    unittest.main()
