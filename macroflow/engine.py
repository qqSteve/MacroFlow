"""Basic action engine. WARNING: actions affect the currently focused desktop."""
from threading import Event
from time import monotonic, sleep

from PySide6.QtCore import QThread, Signal


ACTIONS = {
    "click": "Левый клик",
    "double_click": "Двойной клик",
    "type_text": "Ввод текста",
    "press_key": "Нажать клавишу",
    "wait": "Ожидание",
    "find_text": "Поиск текста (планируется)",
}


class Runner(QThread):
    log = Signal(str)
    step_changed = Signal(int)
    ended = Signal(str)

    def __init__(self, steps, one_step=False):
        super().__init__()
        self.steps = [dict(step) for step in steps]
        self.one_step = one_step
        self.halt = Event()
        self.active = Event()
        self.active.set()

    def stop(self):
        self.halt.set()
        self.active.set()

    def toggle_pause(self):
        if self.active.is_set():
            self.active.clear()
        else:
            self.active.set()

    def _delay(self, ms):
        # Respect pause even for an action with zero delay.
        while not self.active.wait(0.08):
            if self.halt.is_set():
                return False
        until = monotonic() + max(ms, 0) / 1000
        while monotonic() < until:
            if self.halt.is_set():
                return False
            self.active.wait(0.08)
            if not self.active.is_set():
                # Freeze the duration while paused.
                start = monotonic()
                while not self.active.wait(0.08):
                    if self.halt.is_set():
                        return False
                until += monotonic() - start
            sleep(min(0.03, max(0, until - monotonic())))
        return not self.halt.is_set()

    def run(self):
        import pyautogui
        pyautogui.FAILSAFE = True
        try:
            executed = 0
            for i, step in enumerate(self.steps):
                if self.halt.is_set():
                    break
                if not step.get("enabled", True):
                    continue
                if not self._delay(0):
                    break
                self.step_changed.emit(i)
                action = step.get("action")
                if action in ("click", "double_click"):
                    region = step.get("region")
                    if not region:
                        raise ValueError(f"Шаг {i+1}: сначала укажите область кнопки")
                    x = region["x"] + region["w"] // 2
                    y = region["y"] + region["h"] // 2
                    if action == "click":
                        pyautogui.click(x, y)
                    else:
                        pyautogui.doubleClick(x, y, interval=0.12)
                elif action == "type_text":
                    # paste via system clipboard for Cyrillic support, without shell calls
                    # Clipboard operations belong to the Qt main thread; see the UI warning:
                    # for v0.1.0 keep only ASCII via write(), reject Unicode.
                    value = step.get("text", "")
                    if not value.isascii():
                        raise ValueError("Русский текст пока не поддерживается движком. Доработаем вставку через буфер обмена.")
                    pyautogui.write(value, interval=0.015)
                elif action == "press_key":
                    key = step.get("text", "").strip().lower()
                    if not key:
                        raise ValueError(f"Шаг {i+1}: укажите клавишу (например, enter)")
                    pyautogui.press(key)
                elif action == "wait":
                    pass
                else:
                    raise NotImplementedError(f"Шаг {i+1}: действие '{action}' ещё не реализовано")
                self.log.emit(f"Шаг {i+1} завершён: {ACTIONS.get(action, action)}")
                executed += 1
                if not self._delay(int(step.get("delay_ms", 0))):
                    break
                if self.one_step:
                    break
            self.ended.emit("Остановлено" if self.halt.is_set() else f"Готово: {executed} действий")
        except Exception as exc:
            self.ended.emit(f"Ошибка: {exc}")
