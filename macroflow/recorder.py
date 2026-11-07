"""Explicit opt-in event recording. Printable keystrokes are NOT captured.

No credentials or typed text are stored. They must be added manually using
an 'input text' step. Mouse coordinates and selected non-printable keys only.
"""
from PySide6.QtCore import QObject, Signal


class Recorder(QObject):
    shortcut = Signal(str)
    clicked = Signal(int, int)
    pressed = Signal(str)

    def __init__(self):
        super().__init__()
        self.recording = False
        self._keyboard = None
        self._mouse = None

    def start_listeners(self):
        try:
            from pynput import keyboard, mouse
            self._keyboard = keyboard.Listener(on_press=self._on_press)
            self._mouse = mouse.Listener(on_click=self._on_click)
            self._keyboard.start()
            self._mouse.start()
            return True
        except Exception:
            return False

    def stop_listeners(self):
        for listener in (self._keyboard, self._mouse):
            if listener is not None:
                listener.stop()

    def _on_press(self, key):
        name = getattr(key, "name", "")
        if name in {"f6", "f7", "f8", "f9"}:
            self.shortcut.emit(name)
        elif self.recording and name in {"enter", "tab", "esc", "up", "down", "left", "right"}:
            self.pressed.emit(name)

    def _on_click(self, x, y, button, pressed):
        if self.recording and pressed and getattr(button, "name", "") == "left":
            self.clicked.emit(int(x), int(y))
