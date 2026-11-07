"""MacroFlow desktop UI. The same theme is applied to every page."""
import sys
from functools import partial
from time import monotonic

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFrame, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QListWidget, QListWidgetItem, QStackedWidget,
    QLineEdit, QComboBox, QSpinBox, QCheckBox, QMessageBox, QSplitter,
    QFormLayout, QAbstractItemView, QDialog, QInputDialog,
)
from . import APP_NAME, __version__, GITHUB_REPOSITORY
from .theme import STYLE, ACCENT
from .store import load_scripts, save_scripts, fresh_script, fresh_step
from .engine import Runner, ACTIONS
from .recorder import Recorder
from .overlay import RegionSelector
from .updates import UpdateCheck


def label(text, role=None):
    result = QLabel(text)
    if role:
        result.setObjectName(role)
    result.setWordWrap(True)
    return result


def button(text, callback=None, primary=False):
    result = QPushButton(text)
    if primary:
        result.setObjectName("primary")
    if callback:
        result.clicked.connect(callback)
    result.setCursor(Qt.PointingHandCursor)
    return result


def vbox(widget, margin=16, spacing=12):
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(margin, margin, margin, margin)
    layout.setSpacing(spacing)
    return layout


def panel():
    frame = QFrame()
    frame.setObjectName("panel")
    return frame


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"MacroFlow — Automation Studio {__version__}")
        self.resize(1170, 740)
        self.scripts = load_scripts()
        self.current_id = None
        self.runner = None
        self.checker = None
        self.update_url = None
        self.internal_change = False
        self.record_since = monotonic()
        self.recorder = Recorder()
        self.recorder.shortcut.connect(self.on_hotkey)
        self.recorder.clicked.connect(self.on_recorded_click)
        self.recorder.pressed.connect(self.on_recorded_key)

        root = QWidget()
        self.setCentralWidget(root)
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        self.make_nav(root_layout)
        self.pages = QStackedWidget()
        root_layout.addWidget(self.pages, 1)
        self.make_dashboard()
        self.make_editor()
        self.make_settings()
        self.show_page(0)
        self.refresh_scripts()
        self.statusBar().showMessage("Готово · F6 запуск/пауза · F7 запись · F8 стоп · F9 шаг")
        if not self.recorder.start_listeners():
            QMessageBox.warning(self, "Горячие клавиши", "Не удалось запустить глобальные клавиши. Проверь права доступа Windows.")
        QTimer.singleShot(1800, self.check_updates_silent)

    def make_nav(self, root):
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(225)
        layout = vbox(sidebar, 24, 12)
        layout.addWidget(label("MACROFLOW", "brand"))
        subtitle = label("● AUTOMATION STUDIO", "muted")
        subtitle.setStyleSheet(f"color: {ACCENT}; font-size: 10px; font-weight: bold;")
        layout.addWidget(subtitle)
        layout.addSpacing(20)
        self.nav_buttons = []
        for i, text in enumerate(["▦  Мои сценарии", "⚡  Редактор макросов", "⚙  Настройки"]):
            b = button(text, partial(self.show_page, i))
            b.setObjectName("navigation")
            b.setCheckable(True)
            layout.addWidget(b)
            self.nav_buttons.append(b)
        layout.addStretch(1)
        version = label(f"Версия {__version__}", "muted")
        layout.addWidget(version)
        root.addWidget(sidebar)

    def show_page(self, i):
        self.pages.setCurrentIndex(i)
        for j, nav in enumerate(self.nav_buttons):
            nav.setChecked(i == j)

    def make_dashboard(self):
        page = QWidget()
        layout = vbox(page, 26, 18)
        layout.addWidget(label("Мои сценарии", "heading"))
        layout.addWidget(label("Сохраняй макросы, записывай действия и запускай автоматизацию.", "muted"))
        bar = QHBoxLayout()
        bar.addWidget(button("＋ Создать сценарий", self.new_script, True))
        bar.addWidget(button("● Начать запись  F7", self.toggle_record))
        bar.addStretch(1)
        layout.addLayout(bar)
        card = panel()
        card_l = vbox(card)
        h = label("БИБЛИОТЕКА МАКРОСОВ")
        h.setStyleSheet(f"color: {ACCENT}; font-weight: bold;")
        card_l.addWidget(h)
        self.script_list = QListWidget()
        self.script_list.itemDoubleClicked.connect(self.open_selected_script)
        card_l.addWidget(self.script_list)
        card_l.addWidget(label("Двойной клик — открыть сценарий в редакторе.", "muted"))
        layout.addWidget(card, 1)
        layout.addWidget(label("Все данные сценариев сохраняются локально в профиле Windows.", "muted"))
        self.pages.addWidget(page)

    def make_editor(self):
        page = QWidget()
        layout = vbox(page, 22, 12)
        top = QHBoxLayout()
        top.addWidget(label("Редактор макросов", "heading"))
        top.addStretch()
        top.addWidget(button("💾 Сохранить", self.save, True))
        layout.addLayout(top)
        self.script_name = QLineEdit()
        self.script_name.setPlaceholderText("Название сценария")
        self.script_name.editingFinished.connect(self.rename_current)
        layout.addWidget(self.script_name)
        global_row = QHBoxLayout()
        global_row.addWidget(label("Дополнительная общая задержка"))
        self.global_delay = QSpinBox()
        self.global_delay.setRange(0, 120000)
        self.global_delay.setSingleStep(50)
        self.global_delay.setSuffix(" мс")
        self.global_delay.setToolTip("Прибавляется к индивидуальной задержке каждого шага")
        self.global_delay.valueChanged.connect(self.apply_global_delay)
        global_row.addWidget(self.global_delay)
        layout.addLayout(global_row)
        splitter = QSplitter(Qt.Horizontal)
        left = panel()
        ll = vbox(left, 14, 10)
        lh = label("ПОСЛЕДОВАТЕЛЬНОСТЬ ДЕЙСТВИЙ")
        lh.setStyleSheet(f"color: {ACCENT}; font-weight: bold;")
        ll.addWidget(lh)
        self.step_list = QListWidget()
        self.step_list.setDragDropMode(QAbstractItemView.InternalMove)
        self.step_list.setDefaultDropAction(Qt.MoveAction)
        self.step_list.itemSelectionChanged.connect(self.select_step)
        self.step_list.model().rowsMoved.connect(self.reordered_steps)
        ll.addWidget(self.step_list, 1)
        row = QHBoxLayout()
        row.addWidget(button("＋ Добавить", self.add_step, True))
        row.addWidget(button("↑", partial(self.shift_step, -1)))
        row.addWidget(button("↓", partial(self.shift_step, 1)))
        ll.addLayout(row)
        row2 = QHBoxLayout()
        row2.addWidget(button("Копировать", self.duplicate_step))
        row2.addWidget(button("Удалить", self.delete_step))
        ll.addLayout(row2)
        splitter.addWidget(left)
        right = panel()
        rl = vbox(right, 18, 14)
        rh = label("НАСТРОЙКИ ДЕЙСТВИЯ")
        rh.setStyleSheet(f"color: {ACCENT}; font-weight: bold;")
        rl.addWidget(rh)
        form = QFormLayout()
        form.setSpacing(12)
        self.action_field = QComboBox()
        for key, title in ACTIONS.items():
            self.action_field.addItem(title, key)
        self.action_field.currentIndexChanged.connect(self.apply_step_edits)
        form.addRow("Тип действия", self.action_field)
        self.delay_field = QSpinBox()
        self.delay_field.setRange(0, 120000)
        self.delay_field.setSingleStep(50)
        self.delay_field.setSuffix(" мс")
        self.delay_field.valueChanged.connect(self.apply_step_edits)
        form.addRow("Задержка после", self.delay_field)
        self.text_field = QLineEdit()
        self.text_field.setPlaceholderText("Текст или клавиша (например, enter)")
        self.text_field.textChanged.connect(self.apply_step_edits)
        form.addRow("Текст / клавиша", self.text_field)
        self.enabled_field = QCheckBox("Выполнять действие")
        self.enabled_field.stateChanged.connect(self.apply_step_edits)
        form.addRow("Включено", self.enabled_field)
        rl.addLayout(form)
        self.region_label = label("Область не выбрана", "muted")
        rl.addWidget(self.region_label)
        rl.addWidget(button("▣ Выделить область на экране", self.pick_region))
        rl.addWidget(label("Перетаскивай шаги в списке. Задержка задаётся отдельно для каждого шага.", "muted"))
        rl.addStretch(1)
        splitter.addWidget(right)
        splitter.setSizes([480, 470])
        layout.addWidget(splitter, 1)
        controls = QHBoxLayout()
        controls.addWidget(button("▶ Старт / Пауза  F6", self.start_or_pause, True))
        controls.addWidget(button("● Запись  F7", self.toggle_record))
        controls.addWidget(button("■ Стоп  F8", self.stop_runner))
        controls.addWidget(button("⏭ Один шаг  F9", self.run_one))
        layout.addLayout(controls)
        self.log = label("Журнал: ожидание запуска", "muted")
        layout.addWidget(self.log)
        self.pages.addWidget(page)

    def make_settings(self):
        page = QWidget()
        layout = vbox(page, 26, 20)
        layout.addWidget(label("Настройки", "heading"))
        layout.addWidget(label("Те же фирменные цвета и компоненты — на всех экранах.", "muted"))
        card = panel()
        content = vbox(card, 20, 14)
        heading = label("ОБНОВЛЕНИЯ ЧЕРЕЗ GITHUB")
        heading.setStyleSheet(f"color: {ACCENT}; font-weight: bold;")
        content.addWidget(heading)
        content.addWidget(label(f"Репозиторий: {GITHUB_REPOSITORY}"))
        content.addWidget(label(f"Текущая версия: {__version__}"))
        self.update_status = label("Проверка обновлений ещё не выполнена", "muted")
        content.addWidget(self.update_status)
        buttons = QHBoxLayout()
        buttons.addWidget(button("Проверить обновления", partial(self.check_updates, False), True))
        buttons.addWidget(button("Открыть релиз", self.open_release))
        buttons.addStretch()
        content.addLayout(buttons)
        layout.addWidget(card)
        kb = panel()
        kl = vbox(kb)
        title = label("ГОРЯЧИЕ КЛАВИШИ")
        title.setStyleSheet(f"color: {ACCENT}; font-weight: bold;")
        kl.addWidget(title)
        kl.addWidget(label("F6 — старт / пауза     F7 — запись     F8 — стоп     F9 — один шаг"))
        kl.addWidget(label("В этой стартовой версии сочетания пока фиксированные.", "muted"))
        layout.addWidget(kb)
        privacy = panel()
        pl = vbox(privacy)
        title = label("БЕЗОПАСНОСТЬ ЗАПИСИ")
        title.setStyleSheet(f"color: {ACCENT}; font-weight: bold;")
        pl.addWidget(title)
        pl.addWidget(label("Запись только после F7. Захватываются клики и служебные клавиши; текст, пароли и последовательности символов не записываются."))
        pl.addWidget(label("При выполнении действий управление мышью можно экстренно остановить перемещением курсора в угол экрана (PyAutoGUI FAILSAFE).", "muted"))
        layout.addWidget(privacy)
        layout.addStretch()
        self.pages.addWidget(page)

    def refresh_scripts(self):
        self.script_list.clear()
        for script in self.scripts:
            item = QListWidgetItem(f"⚡  {script['name']}      ·      {len(script['steps'])} шагов")
            item.setData(Qt.UserRole, script["id"])
            self.script_list.addItem(item)

    def current_script(self):
        return next((s for s in self.scripts if s["id"] == self.current_id), None)

    def save(self):
        save_scripts(self.scripts)
        self.refresh_scripts()
        self.statusBar().showMessage("Изменения сохранены")

    def new_script(self):
        name, ok = QInputDialog.getText(self, "Новый сценарий", "Название:", text="Новый сценарий")
        if not ok:
            return
        script = fresh_script(name.strip() or "Новый сценарий")
        self.scripts.append(script)
        self.current_id = script["id"]
        self.save()
        self.open_editor()

    def open_selected_script(self, item):
        self.current_id = item.data(Qt.UserRole)
        self.open_editor()

    def open_editor(self):
        script = self.current_script()
        if not script:
            return
        self.script_name.setText(script["name"])
        self.global_delay.blockSignals(True)
        self.global_delay.setValue(int(script.get("global_delay_ms", 0)))
        self.global_delay.blockSignals(False)
        self.refresh_steps()
        self.show_page(1)

    def apply_global_delay(self, value):
        script = self.current_script()
        if script:
            script["global_delay_ms"] = int(value)
            self.save()

    def rename_current(self):
        script = self.current_script()
        if script:
            script["name"] = self.script_name.text().strip() or "Новый сценарий"
            self.save()

    def refresh_steps(self, select_id=None):
        script = self.current_script()
        self.internal_change = True
        self.step_list.clear()
        if script:
            for index, step in enumerate(script["steps"]):
                title = ACTIONS.get(step["action"], step["action"])
                flag = "" if step.get("enabled", True) else " [выкл]"
                item = QListWidgetItem(f"{index+1:02}  {title} · {step.get('delay_ms',0)} мс{flag}")
                item.setData(Qt.UserRole, step["id"])
                self.step_list.addItem(item)
                if select_id == step["id"]:
                    self.step_list.setCurrentItem(item)
        self.internal_change = False
        self.select_step()

    def current_step(self):
        script = self.current_script()
        item = self.step_list.currentItem()
        if not script or not item:
            return None
        return next((s for s in script["steps"] if s["id"] == item.data(Qt.UserRole)), None)

    def select_step(self):
        if self.internal_change:
            return
        step = self.current_step()
        self.internal_change = True
        widgets = [self.action_field, self.delay_field, self.text_field, self.enabled_field]
        for w in widgets:
            w.setEnabled(step is not None)
        if step:
            i = self.action_field.findData(step["action"])
            self.action_field.setCurrentIndex(max(0, i))
            self.delay_field.setValue(int(step.get("delay_ms", 300)))
            self.text_field.setText(step.get("text", ""))
            self.enabled_field.setChecked(step.get("enabled", True))
            self.region_label.setText(f"Область: {step['region']}" if step.get("region") else "Область не выбрана")
        else:
            self.region_label.setText("Выберите действие слева")
        self.internal_change = False

    def apply_step_edits(self, *args):
        if self.internal_change:
            return
        step = self.current_step()
        if not step:
            return
        step["action"] = self.action_field.currentData()
        step["delay_ms"] = self.delay_field.value()
        step["text"] = self.text_field.text()
        step["enabled"] = self.enabled_field.isChecked()
        self.refresh_steps(step["id"])
        self.save()

    def add_step(self):
        if not self.current_script():
            self.new_script()
        script = self.current_script()
        if not script:
            return
        step = fresh_step()
        script["steps"].append(step)
        self.refresh_steps(step["id"])
        self.save()

    def reordered_steps(self, *args):
        if self.internal_change:
            return
        script = self.current_script()
        if not script:
            return
        by_id = {s["id"]: s for s in script["steps"]}
        new_ids = [self.step_list.item(i).data(Qt.UserRole) for i in range(self.step_list.count())]
        if set(new_ids) == set(by_id):
            script["steps"] = [by_id[k] for k in new_ids]
            selected = self.current_step()
            self.refresh_steps(selected["id"] if selected else None)
            self.save()

    def shift_step(self, direction):
        script = self.current_script()
        if not script:
            return
        row = self.step_list.currentRow()
        other = row + direction
        if 0 <= row < len(script["steps"]) and 0 <= other < len(script["steps"]):
            script["steps"][row], script["steps"][other] = script["steps"][other], script["steps"][row]
            self.refresh_steps(script["steps"][other]["id"])
            self.save()

    def duplicate_step(self):
        import copy
        from uuid import uuid4
        step = self.current_step()
        script = self.current_script()
        if step and script:
            copied = copy.deepcopy(step)
            copied["id"] = str(uuid4())
            script["steps"].insert(self.step_list.currentRow()+1, copied)
            self.refresh_steps(copied["id"])
            self.save()

    def delete_step(self):
        script, step = self.current_script(), self.current_step()
        if script and step:
            script["steps"] = [s for s in script["steps"] if s["id"] != step["id"]]
            self.refresh_steps()
            self.save()

    def pick_region(self):
        step = self.current_step()
        if not step:
            return
        self.hide()
        QApplication.processEvents()
        overlay = RegionSelector()
        result = overlay.exec()
        self.show()
        self.raise_()
        if result == QDialog.Accepted:
            step["region"] = overlay.region
            self.region_label.setText(f"Область: {overlay.region}")
            self.save()

    def runner_ended(self, message):
        self.log.setText("Журнал: " + message)
        self.statusBar().showMessage(message)
        self.runner = None

    def launch_runner(self, one_step=False):
        script = self.current_script()
        if not script:
            self.statusBar().showMessage("Сначала выберите сценарий")
            return
        if self.recorder.recording:
            self.toggle_record()
        if self.runner is not None:
            return
        # Per-step delays and the scenario-wide delay are additive.
        steps = [{**s, "delay_ms": int(s.get("delay_ms", 0)) + int(script.get("global_delay_ms", 0))}
                 for s in script["steps"]]
        if one_step:
            row = max(0, self.step_list.currentRow())
            steps = steps[row:row+1]
        if not steps:
            self.statusBar().showMessage("В сценарии пока нет действий")
            return
        self.runner = Runner(steps, one_step)
        self.runner.log.connect(self.log.setText)
        self.runner.step_changed.connect(lambda i: self.statusBar().showMessage(f"Выполняется шаг {i+1}"))
        self.runner.ended.connect(self.runner_ended)
        self.runner.start()

    def start_or_pause(self):
        if self.runner is None:
            self.launch_runner()
        else:
            self.runner.toggle_pause()
            self.statusBar().showMessage("Пауза / продолжение переключено")

    def run_one(self):
        if self.runner is None:
            self.launch_runner(one_step=True)

    def stop_runner(self):
        if self.runner is not None:
            self.runner.stop()
            self.statusBar().showMessage("Запрошена экстренная остановка")

    def on_hotkey(self, key):
        {"f6": self.start_or_pause, "f7": self.toggle_record,
         "f8": self.stop_runner, "f9": self.run_one}[key]()

    def toggle_record(self):
        if self.runner is not None:
            self.statusBar().showMessage("Сначала остановите выполнение")
            return
        if not self.current_script():
            script = fresh_script("Записанный сценарий")
            self.scripts.append(script)
            self.current_id = script["id"]
            self.save()
            self.open_editor()
        self.recorder.recording = not self.recorder.recording
        self.record_since = monotonic()
        if self.recorder.recording:
            self.statusBar().showMessage("● ЗАПИСЬ — F7 для завершения. Текст не записывается.")
            self.showMinimized()
        else:
            self.save()
            self.open_editor()
            self.showNormal()
            self.raise_()
            self.statusBar().showMessage("Запись остановлена. Проверьте и отредактируйте шаги.")

    def append_recorded_step(self, action, x=None, y=None, key=None):
        script = self.current_script()
        if not self.recorder.recording or not script:
            return
        # Do not accidentally record clicks on our own window.
        if x is not None and not self.isMinimized() and self.geometry().contains(x, y):
            return
        step = fresh_step(action)
        if x is not None:
            step["region"] = {"x": x-5, "y": y-5, "w": 10, "h": 10}
        if key is not None:
            step["text"] = key
        # Recorded intervals belong AFTER the previous action, as in the runner.
        if script["steps"]:
            script["steps"][-1]["delay_ms"] = min(120000, int((monotonic()-self.record_since)*1000))
        step["delay_ms"] = 300
        self.record_since = monotonic()
        script["steps"].append(step)
        self.refresh_steps(step["id"])

    def on_recorded_click(self, x, y):
        self.append_recorded_step("click", x=x, y=y)

    def on_recorded_key(self, key):
        self.append_recorded_step("press_key", key=key)

    def check_updates_silent(self):
        self.check_updates(silent=True)

    def check_updates(self, silent=False):
        if self.checker is not None and self.checker.isRunning():
            return
        self.update_status.setText("Проверяем GitHub Releases…")
        self.checker = UpdateCheck()
        self.checker.result.connect(partial(self.update_result, silent=silent))
        self.checker.error.connect(partial(self.update_error, silent=silent))
        self.checker.start()

    def update_result(self, version, url, has_update, silent=False):
        self.update_url = url
        msg = f"Доступна версия {version}" if has_update else f"Установлена актуальная версия ({__version__})"
        self.update_status.setText(msg)
        self.statusBar().showMessage(msg)
        if has_update and not silent:
            reply = QMessageBox.question(self, "Обновление", f"{msg}. Открыть страницу релиза для скачивания?")
            if reply == QMessageBox.Yes:
                self.open_release()

    def update_error(self, message, silent=False):
        self.update_status.setText("Не удалось проверить релизы. Возможно, репозиторий ещё не создан.")
        if not silent:
            QMessageBox.information(self, "Проверка обновлений", f"Сервис пока недоступен:\n{message}")

    def open_release(self):
        QDesktopServices.openUrl(QUrl(self.update_url or f"https://github.com/{GITHUB_REPOSITORY}/releases"))

    def closeEvent(self, event):
        if self.runner is not None and self.runner.isRunning():
            self.stop_runner()
            self.runner.wait(2000)
            if self.runner.isRunning():
                event.ignore()
                QMessageBox.warning(self, "Подождите", "Дождитесь остановки текущего действия.")
                return
        self.recorder.recording = False
        self.recorder.stop_listeners()
        self.save()
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyleSheet(STYLE)
    try:
        window = MainWindow()
    except RuntimeError as exc:
        QMessageBox.critical(None, "MacroFlow", str(exc))
        return 1
    window.show()
    return app.exec()
