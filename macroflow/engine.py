"""Desktop automation runner with pause, stop, and scenario repeat modes.

CAUTION: actions target the foreground desktop. Test on non-production documents.
"""
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
    cycle_changed = Signal(int, int)  # finished cycles, total (0 for infinite)
    ended = Signal(str)

    def __init__(self, steps, one_step=False, repeat_mode="once", repeat_count=1,
                 cycle_delay_ms=0, start_index=0):
        super().__init__()
        self.steps = [dict(step) for step in steps]
        self.one_step = bool(one_step)
        self.repeat_mode = repeat_mode if repeat_mode in ("once", "count", "forever") else "once"
        self.repeat_count = max(1, min(1000000, int(repeat_count)))
        self.cycle_delay_ms = max(0, min(120000, int(cycle_delay_ms)))
        self.start_index = int(start_index)
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
        """Interruptible wait; elapsed pause time does not consume the delay."""
        ms = max(0, int(ms))
        remaining = ms / 1000
        while not self.halt.is_set():
            if not self.active.wait(0.04):
                continue
            if remaining <= 0:
                return True
            wait_for = min(remaining, 0.04)
            start = monotonic()
            sleep(wait_for)
            remaining -= monotonic() - start
        return False

    def _perform(self, pyautogui, step, index):
        action = step.get("action")
        if action in ("click", "double_click"):
            region = step.get("region")
            if not region:
                raise ValueError(f"Шаг {index+1}: сначала укажите область кнопки")
            x = region["x"] + region["w"] // 2
            y = region["y"] + region["h"] // 2
            if action == "click":
                pyautogui.click(x, y)
            else:
                pyautogui.doubleClick(x, y, interval=0.12)
        elif action == "type_text":
            value = step.get("text", "")
            if not value.isascii():
                raise ValueError("Русский текст пока не поддерживается. Используйте латиницу или горячие клавиши.")
            pyautogui.write(value, interval=0.015)
        elif action == "press_key":
            key = step.get("text", "").strip().lower()
            if not key:
                raise ValueError(f"Шаг {index+1}: укажите клавишу (например, enter)")
            pyautogui.press(key)
        elif action == "wait":
            pass  # delay after the step defines the wait duration
        else:
            raise NotImplementedError(f"Шаг {index+1}: действие '{action}' пока не реализовано")

    def run(self):
        import pyautogui
        pyautogui.FAILSAFE = True
        completed_cycles = 0
        executed_steps = 0
        enabled = [(i, s) for i, s in enumerate(self.steps) if s.get("enabled", True)]
        if not enabled:
            self.ended.emit("Нет включённых действий: сценарий не запускался")
            return
        total = 1 if self.one_step or self.repeat_mode == "once" else (
            self.repeat_count if self.repeat_mode == "count" else 0)
        try:
            while not self.halt.is_set() and (total == 0 or completed_cycles < total):
                for i, step in enabled:
                    if not self._delay(0):
                        break
                    self.step_changed.emit(self.start_index + i)
                    self._perform(pyautogui, step, i)
                    executed_steps += 1
                    self.log.emit(f"Цикл {completed_cycles+1} · шаг {i+1}: {ACTIONS.get(step.get('action'))}")
                    if not self._delay(step.get("delay_ms", 0)):
                        break
                    if self.one_step:
                        break
                if self.halt.is_set():
                    break
                completed_cycles += 1
                self.cycle_changed.emit(completed_cycles, total)
                if self.one_step or (total != 0 and completed_cycles >= total):
                    break
                if not self._delay(max(self.cycle_delay_ms, 15 if total == 0 else 0)):
                    break
            if self.halt.is_set():
                self.ended.emit(f"Остановлено · завершено циклов: {completed_cycles}")
            else:
                self.ended.emit(f"Готово · циклов: {completed_cycles}, действий: {executed_steps}")
        except Exception as exc:
            self.ended.emit(f"Ошибка на цикле {completed_cycles+1}: {exc}")
