"""MacroFlow desktop interface: shared design system, editor and scenario library."""
import copy
import sys
from datetime import datetime
from functools import partial
from pathlib import Path
from time import monotonic
from uuid import uuid4

from PySide6.QtCore import Qt, QTimer, QUrl, QSize
from PySide6.QtGui import QDesktopServices, QFont, QFontDatabase, QIcon
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFrame, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QListWidget, QListWidgetItem, QStackedWidget,
    QLineEdit, QComboBox, QSpinBox, QCheckBox, QMessageBox, QSplitter,
    QFormLayout, QAbstractItemView, QDialog, QInputDialog, QFileDialog, QMenu,
)

from . import APP_NAME, __version__, GITHUB_REPOSITORY
from .theme import stylesheet, FONT_PREFERENCES, ACCENT, asset_path
from .store import data_directory, fresh_script, fresh_step, load_scripts, save_scripts
from .exchange import parse_file, write_file
from .templates import TEMPLATES, build_template
from .engine import Runner, ACTIONS
from .recorder import Recorder
from .overlay import RegionSelector
from .updates import UpdateCheck


def label(text, role=None):
    result = QLabel(text)
    result.setTextFormat(Qt.PlainText)
    if role:
        result.setObjectName(role)
    result.setWordWrap(True)
    return result


def button(text, callback=None, primary=False, role=None):
    result = QPushButton(text)
    if primary:
        result.setObjectName("primary")
    elif role:
        result.setObjectName(role)
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


def orange_heading(text):
    return label(text, "sectionTitle")


def spinbox(suffix, maximum=120000):
    widget = QSpinBox()
    widget.setRange(0, maximum)
    widget.setSingleStep(50 if maximum > 10000 else 1)
    widget.setSuffix(suffix)
    widget.setMinimumWidth(113)
    return widget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"MacroFlow — Automation Studio {__version__}")
        self.setWindowIcon(QIcon(str(asset_path("macroflow.ico"))))
        self.resize(1250, 820)
        self.setMinimumSize(1040, 680)
        self.scripts = load_scripts()
        self.current_id = None
        self.running_script_id = None
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
            QMessageBox.warning(self, "Горячие клавиши", "Глобальные клавиши не запущены. Проверьте разрешения Windows.")
        QTimer.singleShot(1800, self.check_updates_silent)

    def make_nav(self, root):
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(242)
        layout = vbox(sidebar, 16, 13)
        brand = QFrame()
        brand.setObjectName("sidebarBrand")
        b = vbox(brand, 15, 4)
        b.addWidget(label("MACROFLOW", "brand"))
        tagline = label("● AUTOMATION STUDIO")
        tagline.setStyleSheet(f"color: {ACCENT}; font-size: 11px; font-weight: 800;")
        b.addWidget(tagline)
        layout.addWidget(brand)
        layout.addSpacing(11)
        layout.addWidget(orange_heading("НАВИГАЦИЯ"))
        self.nav_buttons = []
        for i, title in enumerate(("▦   Мои сценарии", "⚡   Редактор макросов", "⚙   Настройки")):
            btn = button(title, partial(self.show_page, i))
            btn.setObjectName("navigation")
            btn.setCheckable(True)
            layout.addWidget(btn)
            self.nav_buttons.append(btn)
        layout.addStretch()
        layout.addWidget(orange_heading("УПРАВЛЕНИЕ"))
        layout.addWidget(label("F6 · Запуск / пауза\nF7 · Запись действий\nF8 · Остановить\nF9 · Один шаг", "muted"))
        layout.addSpacing(7)
        layout.addWidget(label(f"MACROFLOW   •   v{__version__}", "muted"))
        root.addWidget(sidebar)

    def show_page(self, index):
        self.pages.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(index == i)

    def make_dashboard(self):
        page = QWidget()
        layout = vbox(page, 25, 15)
        layout.addWidget(label("Мои сценарии", "heading"))
        layout.addWidget(label("Управляй сценариями, записывай действия и обменивайся макросами.", "muted"))
        actions = QHBoxLayout()
        actions.setSpacing(8)
        actions.addWidget(button("＋ Новый сценарий", self.new_script, True))
        actions.addWidget(button("▦ Из шаблона", self.new_from_template))
        actions.addWidget(button("↧ Импорт .mflow", self.import_scripts))
        actions.addWidget(button("↥ Экспорт всех", self.export_all_scripts))
        actions.addStretch()
        layout.addLayout(actions)

        holder = panel()
        box = vbox(holder, 16, 12)
        box.addWidget(orange_heading("БИБЛИОТЕКА СЦЕНАРИЕВ"))
        self.script_list = QListWidget()
        self.script_list.setObjectName("scenarioList")
        self.script_list.setSpacing(3)
        self.script_list.itemDoubleClicked.connect(self.open_selected_script)
        self.script_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.script_list.customContextMenuRequested.connect(self.show_script_menu)
        box.addWidget(self.script_list, 1)
        box.addWidget(label("Двойной клик — редактировать. Правый клик — меню действий с выбранным сценарием.", "muted"))
        layout.addWidget(holder, 1)
        layout.addWidget(label("Сценарии хранятся локально и остаются после обновлений MacroFlow.", "muted"))
        self.pages.addWidget(page)

    def make_editor(self):
        page = QWidget()
        layout = vbox(page, 18, 11)
        header = QHBoxLayout()
        header.addWidget(label("Редактор макросов", "heading"))
        header.addStretch()
        header.addWidget(button("◆ Сохранить сценарий", self.save, True))
        layout.addLayout(header)

        info = QHBoxLayout()
        self.script_name = QLineEdit()
        self.script_name.setPlaceholderText("Название сценария")
        self.script_name.setToolTip("Название для библиотеки макросов")
        self.script_name.editingFinished.connect(self.rename_current)
        info.addWidget(self.script_name, 2)
        self.script_description = QLineEdit()
        self.script_description.setPlaceholderText("Описание сценария (необязательно)")
        self.script_description.editingFinished.connect(self.describe_current)
        info.addWidget(self.script_description, 3)
        layout.addLayout(info)

        parameters = panel()
        p = vbox(parameters, 13, 9)
        p.addWidget(orange_heading("ЗАПУСК И ПОВТОРЕНИЯ"))
        options = QHBoxLayout()
        options.setSpacing(13)
        options.addWidget(label("Повтор"))
        self.repeat_mode = QComboBox()
        self.repeat_mode.addItem("Один раз", "once")
        self.repeat_mode.addItem("Заданное число", "count")
        self.repeat_mode.addItem("Бесконечно", "forever")
        self.repeat_mode.setMinimumWidth(148)
        self.repeat_mode.currentIndexChanged.connect(self.apply_repeat_settings)
        options.addWidget(self.repeat_mode, 2)
        options.addWidget(label("Циклов"))
        self.repeat_count = spinbox("", 1000000)
        self.repeat_count.setMinimum(1)
        self.repeat_count.valueChanged.connect(self.apply_repeat_settings)
        options.addWidget(self.repeat_count, 1)
        options.addWidget(label("Между циклами"))
        self.cycle_delay = spinbox(" мс")
        self.cycle_delay.setToolTip("Пауза после полного прохода по сценарию")
        self.cycle_delay.valueChanged.connect(self.apply_repeat_settings)
        options.addWidget(self.cycle_delay, 1)
        options.addWidget(label("Общая задержка"))
        self.global_delay = spinbox(" мс")
        self.global_delay.setToolTip("Добавляется к задержке каждого шага")
        self.global_delay.valueChanged.connect(self.apply_repeat_settings)
        options.addWidget(self.global_delay, 1)
        p.addLayout(options)
        layout.addWidget(parameters)

        splitter = QSplitter(Qt.Horizontal)
        left = panel()
        ll = vbox(left, 14, 10)
        ll.addWidget(orange_heading("ПОСЛЕДОВАТЕЛЬНОСТЬ ДЕЙСТВИЙ"))
        self.step_list = QListWidget()
        self.step_list.setDragDropMode(QAbstractItemView.InternalMove)
        self.step_list.setDefaultDropAction(Qt.MoveAction)
        self.step_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.step_list.itemSelectionChanged.connect(self.select_step)
        self.step_list.model().rowsMoved.connect(self.reordered_steps)
        ll.addWidget(self.step_list, 1)
        first = QHBoxLayout()
        first.addWidget(button("＋ Добавить", self.add_step, True))
        first.addWidget(button("↑", partial(self.shift_step, -1)))
        first.addWidget(button("↓", partial(self.shift_step, 1)))
        ll.addLayout(first)
        second = QHBoxLayout()
        second.addWidget(button("Копировать", self.duplicate_step))
        second.addWidget(button("Удалить", self.delete_step, role="danger"))
        ll.addLayout(second)
        splitter.addWidget(left)

        right = panel()
        rl = vbox(right, 17, 13)
        rl.addWidget(orange_heading("НАСТРОЙКИ ДЕЙСТВИЯ"))
        form = QFormLayout()
        form.setHorizontalSpacing(13)
        form.setVerticalSpacing(13)
        self.action_field = QComboBox()
        for key, title in ACTIONS.items():
            self.action_field.addItem(title, key)
        self.action_field.currentIndexChanged.connect(self.apply_step_edits)
        form.addRow("Тип действия", self.action_field)
        self.delay_field = spinbox(" мс")
        self.delay_field.valueChanged.connect(self.apply_step_edits)
        form.addRow("Задержка после", self.delay_field)
        self.text_field = QLineEdit()
        self.text_field.setPlaceholderText("Текст / клавиша (например, enter)")
        self.text_field.textChanged.connect(self.apply_step_edits)
        form.addRow("Текст / клавиша", self.text_field)
        self.enabled_field = QCheckBox("Выполнять действие")
        self.enabled_field.stateChanged.connect(self.apply_step_edits)
        form.addRow("Включено", self.enabled_field)
        rl.addLayout(form)
        self.region_label = label("Область не выбрана", "muted")
        rl.addWidget(self.region_label)
        rl.addWidget(button("▣ Выделить область на экране", self.pick_region))
        rl.addWidget(label("Меняй порядок мышью или стрелками ↑ ↓. Значения задержек задаются в миллисекундах.", "muted"))
        rl.addStretch()
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 11)
        splitter.setStretchFactor(1, 10)
        layout.addWidget(splitter, 1)

        controls = QHBoxLayout()
        controls.setSpacing(9)
        controls.addWidget(button("▶ Старт / Пауза  F6", self.start_or_pause, True))
        controls.addWidget(button("● Запись  F7", self.toggle_record))
        controls.addWidget(button("■ Стоп  F8", self.stop_runner, role="danger"))
        controls.addWidget(button("⏭ Один шаг  F9", self.run_one))
        layout.addLayout(controls)
        self.log = label("Журнал: ожидание запуска", "muted")
        layout.addWidget(self.log)
        self.pages.addWidget(page)

    def make_settings(self):
        page = QWidget()
        layout = vbox(page, 27, 18)
        layout.addWidget(label("Настройки", "heading"))
        layout.addWidget(label("Единый графитово-оранжевый стиль на всех страницах приложения.", "muted"))

        card = panel()
        content = vbox(card, 19, 12)
        content.addWidget(orange_heading("ОБНОВЛЕНИЯ ЧЕРЕЗ GITHUB"))
        content.addWidget(label(f"Репозиторий: {GITHUB_REPOSITORY}     ·     Версия: {__version__}"))
        self.update_status = label("Проверка обновлений ещё не выполнена", "muted")
        content.addWidget(self.update_status)
        row = QHBoxLayout()
        row.addWidget(button("Проверить обновления", partial(self.check_updates, False), True))
        row.addWidget(button("Открыть релизы", self.open_release))
        row.addStretch()
        content.addLayout(row)
        layout.addWidget(card)

        kb = panel()
        kl = vbox(kb)
        kl.addWidget(orange_heading("ГЛОБАЛЬНЫЕ ГОРЯЧИЕ КЛАВИШИ"))
        kl.addWidget(label("F6 — запуск / пауза     ·     F7 — запись     ·     F8 — стоп     ·     F9 — один шаг"))
        kl.addWidget(label("Клавиши действуют и при свёрнутом окне. В этой версии их переназначение не реализовано.", "muted"))
        layout.addWidget(kb)

        privacy = panel()
        pl = vbox(privacy)
        pl.addWidget(orange_heading("ПЕРЕД ЗАПУСКОМ"))
        pl.addWidget(label("Импортированные сценарии никогда не запускаются автоматически. Проверьте каждый шаг перед началом."))
        pl.addWidget(label("Рекордер сохраняет только клики и отдельные служебные клавиши; вводимые пароли и обычный текст не записывает.", "muted"))
        pl.addWidget(label("Режим бесконечного повтора требует подтверждения перед запуском. F8 останавливает выполнение; аварийная остановка PyAutoGUI — угол экрана.", "muted"))
        layout.addWidget(privacy)
        layout.addStretch()
        self.pages.addWidget(page)

    # ---- Scenario library and .mflow interchange -----------------------------
    def refresh_scripts(self):
        selected = self.current_id
        self.script_list.clear()
        for script in self.scripts:
            item = QListWidgetItem()
            item.setData(Qt.UserRole, script["id"])
            item.setSizeHint(QSize(120, 73))
            self.script_list.addItem(item)
            entry = QWidget()
            entry.setAttribute(Qt.WA_TransparentForMouseEvents, True)
            entry.setObjectName("scenarioContents")
            line = QVBoxLayout(entry)
            line.setContentsMargins(14, 7, 8, 7)
            line.setSpacing(4)
            title = label("◆  " + script.get("name", "Без названия"), "scenarioTitle")
            title.setWordWrap(False)
            line.addWidget(title)
            description = script.get("description") or "Нет описания · двойной клик для редактирования"
            changed = script.get("updated_at")
            if changed:
                try:
                    description += "    ·    " + datetime.fromisoformat(changed).strftime("%d.%m.%Y")
                except ValueError:
                    pass
            subtitle = label(description, "scenarioSubtitle")
            subtitle.setWordWrap(False)
            line.addWidget(subtitle)
            self.script_list.setItemWidget(item, entry)
            if script["id"] == selected:
                self.script_list.setCurrentItem(item)

    def current_script(self):
        return next((s for s in self.scripts if s["id"] == self.current_id), None)

    def save(self):
        script = self.current_script()
        if script:
            script["updated_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
        save_scripts(self.scripts)
        self.refresh_scripts()
        self.statusBar().showMessage("Изменения сохранены")

    def new_script(self):
        name, ok = QInputDialog.getText(self, "Новый сценарий", "Название:", text="Новый сценарий")
        if not ok:
            return
        self.add_new_script(fresh_script(name.strip() or "Новый сценарий"))

    def new_from_template(self):
        name, ok = QInputDialog.getItem(self, "Сценарий из шаблона", "Выберите шаблон:", list(TEMPLATES), 0, False)
        if ok:
            self.add_new_script(build_template(name))
            QMessageBox.information(self, "Шаблон создан", "Действия шаблона выключены до настройки. Выделите области и включите нужные шаги.")

    def add_new_script(self, script):
        self.scripts.append(script)
        self.current_id = script["id"]
        self.save()
        self.open_editor()

    def open_selected_script(self, item):
        if item:
            self.current_id = item.data(Qt.UserRole)
            self.open_editor()

    def show_script_menu(self, pos):
        item = self.script_list.itemAt(pos)
        if item is None:
            return
        script_id = item.data(Qt.UserRole)
        self.script_list.setCurrentItem(item)
        menu = QMenu(self)
        edit_action = menu.addAction("✎  Изменить")
        rename_action = menu.addAction("✎  Переименовать")
        copy_action = menu.addAction("▣  Копировать")
        export_action = menu.addAction("↥  Экспортировать .mflow")
        menu.addSeparator()
        folder_action = menu.addAction("▤  Показать папку сценариев")
        delete_action = menu.addAction("✕  Удалить")
        selected = menu.exec(self.script_list.viewport().mapToGlobal(pos))
        if selected is None:
            return
        self.current_id = script_id
        if selected is edit_action:
            self.open_editor()
        elif selected is rename_action:
            self.rename_script_dialog(script_id)
        elif selected is copy_action:
            self.duplicate_script(script_id)
        elif selected is export_action:
            self.export_scripts([self.current_script()])
        elif selected is folder_action:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(data_directory())))
        elif selected is delete_action:
            self.delete_script(script_id)

    def rename_script_dialog(self, script_id):
        script = next((s for s in self.scripts if s["id"] == script_id), None)
        if not script:
            return
        new, ok = QInputDialog.getText(self, "Переименовать сценарий", "Новое название:", text=script["name"])
        if ok and new.strip():
            script["name"] = new.strip()
            self.save()
            if self.current_id == script_id:
                self.script_name.setText(script["name"])

    def duplicate_script(self, script_id):
        original = next((s for s in self.scripts if s["id"] == script_id), None)
        if not original:
            return
        duplicate = copy.deepcopy(original)
        duplicate["id"] = str(uuid4())
        duplicate["name"] = original["name"] + " (копия)"
        for step in duplicate["steps"]:
            step["id"] = str(uuid4())
        self.scripts.append(duplicate)
        self.current_id = duplicate["id"]
        self.save()
        self.statusBar().showMessage("Копия сценария создана")

    def delete_script(self, script_id):
        script = next((s for s in self.scripts if s["id"] == script_id), None)
        if not script:
            return
        answer = QMessageBox.question(self, "Удалить сценарий?", f"Удалить «{script['name']}»?\nЭто действие нельзя отменить.", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer != QMessageBox.Yes:
            return
        self.scripts = [s for s in self.scripts if s["id"] != script_id]
        if self.current_id == script_id:
            self.current_id = None
            self.script_name.clear()
            self.script_description.clear()
            self.refresh_steps()
            self.show_page(0)
        self.save()

    def export_scripts(self, scripts):
        if not scripts:
            QMessageBox.information(self, "Экспорт", "Нет сценариев для экспорта.")
            return
        basename = scripts[0]["name"] if len(scripts) == 1 else "MacroFlow-all-scenarios"
        safe = "".join(c for c in basename if c.isalnum() or c in " _-").strip()[:70] or "MacroFlow"
        path, _ = QFileDialog.getSaveFileName(self, "Экспорт сценариев", safe + ".mflow", "MacroFlow (*.mflow);;JSON (*.json)")
        if not path:
            return
        if Path(path).suffix.lower() not in (".mflow", ".json"):
            path += ".mflow"
        try:
            write_file(path, scripts)
        except (OSError, ValueError) as exc:
            QMessageBox.critical(self, "Ошибка экспорта", str(exc))
            return
        self.statusBar().showMessage(f"Экспортировано: {len(scripts)}")
        QMessageBox.information(self, "Экспорт завершён", f"Сохранено сценариев: {len(scripts)}\n{path}")

    def export_all_scripts(self):
        self.export_scripts(self.scripts)

    def import_scripts(self):
        path, _ = QFileDialog.getOpenFileName(self, "Импорт сценария", "", "MacroFlow (*.mflow *.json);;Все файлы (*)")
        if not path:
            return
        try:
            loaded = parse_file(path)
        except (OSError, ValueError, TypeError, UnicodeError) as exc:
            QMessageBox.critical(self, "Ошибка импорта", f"Не удалось импортировать файл:\n{exc}")
            return
        names = {s["name"] for s in self.scripts}
        for script in loaded:
            if script["name"] in names:
                base = script["name"] + " (импорт)"
                name = base
                count = 2
                while name in names:
                    name = f"{base} {count}"
                    count += 1
                script["name"] = name
            names.add(script["name"])
        self.scripts.extend(loaded)
        self.current_id = loaded[0]["id"]
        self.save()
        QMessageBox.information(self, "Импорт завершён", f"Добавлено сценариев: {len(loaded)}.\nПроверьте все действия перед запуском.")
        self.show_page(0)

    # ---- Editor --------------------------------------------------------------
    def open_editor(self):
        script = self.current_script()
        if script is None:
            self.show_page(0)
            return
        self.internal_change = True
        self.script_name.setText(script["name"])
        self.script_description.setText(script.get("description", ""))
        self.global_delay.setValue(int(script.get("global_delay_ms", 0)))
        self.cycle_delay.setValue(int(script.get("cycle_delay_ms", 0)))
        self.repeat_count.setValue(int(script.get("repeat_count", 1)))
        index = self.repeat_mode.findData(script.get("repeat_mode", "once"))
        self.repeat_mode.setCurrentIndex(max(0, index))
        self.repeat_count.setEnabled(self.repeat_mode.currentData() == "count")
        self.internal_change = False
        self.refresh_steps()
        self.show_page(1)

    def apply_repeat_settings(self, *args):
        self.repeat_count.setEnabled(self.repeat_mode.currentData() == "count")
        if self.internal_change:
            return
        script = self.current_script()
        if script is None:
            return
        script.update(repeat_mode=self.repeat_mode.currentData(),
                      repeat_count=self.repeat_count.value(),
                      cycle_delay_ms=self.cycle_delay.value(),
                      global_delay_ms=self.global_delay.value())
        self.save()

    def rename_current(self):
        script = self.current_script()
        if script is not None:
            script["name"] = self.script_name.text().strip() or "Новый сценарий"
            self.save()

    def describe_current(self):
        script = self.current_script()
        if script is not None:
            script["description"] = self.script_description.text().strip()[:300]
            self.save()

    def refresh_steps(self, select_id=None):
        script = self.current_script()
        self.internal_change = True
        self.step_list.clear()
        if script:
            for number, step in enumerate(script["steps"], 1):
                title = ACTIONS.get(step["action"], step["action"])
                flag = "" if step.get("enabled", True) else "  ·  ВЫКЛ"
                item = QListWidgetItem(f"{number:02}    {title}    ·    {step.get('delay_ms', 0)} мс{flag}")
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
        controls = (self.action_field, self.delay_field, self.text_field, self.enabled_field)
        for control in controls:
            control.setEnabled(step is not None)
        if step:
            index = self.action_field.findData(step["action"])
            self.action_field.setCurrentIndex(max(0, index))
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
        step.update(action=self.action_field.currentData(), delay_ms=self.delay_field.value(),
                    text=self.text_field.text(), enabled=self.enabled_field.isChecked())
        self.refresh_steps(step["id"])
        self.save()

    def add_step(self):
        if self.current_script() is None:
            self.new_script()
        script = self.current_script()
        if script is None:
            return
        new = fresh_step()
        script["steps"].append(new)
        self.refresh_steps(new["id"])
        self.save()

    def reordered_steps(self, *args):
        if self.internal_change:
            return
        script = self.current_script()
        if script is None:
            return
        by_id = {s["id"]: s for s in script["steps"]}
        new_ids = [self.step_list.item(i).data(Qt.UserRole) for i in range(self.step_list.count())]
        if len(new_ids) == len(by_id) and set(new_ids) == set(by_id):
            selected = self.step_list.currentItem()
            selected_id = selected.data(Qt.UserRole) if selected else None
            script["steps"] = [by_id[k] for k in new_ids]
            self.refresh_steps(selected_id)
            self.save()

    def shift_step(self, direction):
        script = self.current_script()
        if not script:
            return
        i = self.step_list.currentRow()
        j = i + direction
        if 0 <= i < len(script["steps"]) and 0 <= j < len(script["steps"]):
            script["steps"][i], script["steps"][j] = script["steps"][j], script["steps"][i]
            self.refresh_steps(script["steps"][j]["id"])
            self.save()

    def duplicate_step(self):
        step = self.current_step()
        script = self.current_script()
        if step and script:
            duplicate = copy.deepcopy(step)
            duplicate["id"] = str(uuid4())
            script["steps"].insert(self.step_list.currentRow() + 1, duplicate)
            self.refresh_steps(duplicate["id"])
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

    # ---- Runner and recorder -------------------------------------------------
    def runner_ended(self, message):
        self.log.setText("Журнал: " + message)
        self.statusBar().showMessage(message)

    def runner_finished(self):
        runner = self.runner
        self.runner = None
        self.running_script_id = None
        if runner:
            runner.deleteLater()

    def show_running_step(self, index):
        self.statusBar().showMessage(f"Выполняется шаг {index+1}")
        if self.current_id == self.running_script_id and self.pages.currentIndex() == 1:
            if 0 <= index < self.step_list.count():
                self.step_list.setCurrentRow(index)

    def update_cycle_progress(self, completed, total):
        suffix = str(total) if total else "∞"
        self.statusBar().showMessage(f"Сценарий: завершено циклов {completed}/{suffix}")

    def launch_runner(self, one_step=False):
        script = self.current_script()
        if script is None:
            self.statusBar().showMessage("Сначала выберите сценарий")
            return
        if self.recorder.recording:
            self.toggle_record()
        if self.runner is not None:
            return
        steps = [{**s, "delay_ms": int(s.get("delay_ms", 0)) + int(script.get("global_delay_ms", 0))}
                 for s in script["steps"]]
        start_index = 0
        if one_step:
            start_index = max(0, self.step_list.currentRow())
            steps = steps[start_index:start_index + 1]
        if not steps or not any(s.get("enabled", True) for s in steps):
            self.statusBar().showMessage("Нет включённых действий для запуска")
            return
        mode = "once" if one_step else script.get("repeat_mode", "once")
        if mode == "forever":
            confirm = QMessageBox.question(self, "Бесконечный повтор", "Сценарий будет выполняться до нажатия F8.\nУбедитесь, что действия безопасны. Запустить?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if confirm != QMessageBox.Yes:
                return
        self.running_script_id = script["id"]
        self.runner = Runner(steps, one_step=one_step, repeat_mode=mode,
                             repeat_count=script.get("repeat_count", 1),
                             cycle_delay_ms=script.get("cycle_delay_ms", 0),
                             start_index=start_index)
        self.runner.log.connect(self.log.setText)
        self.runner.step_changed.connect(self.show_running_step)
        self.runner.cycle_changed.connect(self.update_cycle_progress)
        self.runner.ended.connect(self.runner_ended)
        self.runner.finished.connect(self.runner_finished)
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
            self.statusBar().showMessage("Запрошена остановка · F8")

    def on_hotkey(self, key):
        actions = {"f6": self.start_or_pause, "f7": self.toggle_record,
                   "f8": self.stop_runner, "f9": self.run_one}
        callback = actions.get(key)
        if callback:
            callback()

    def toggle_record(self):
        if self.runner is not None:
            self.statusBar().showMessage("Сначала остановите выполнение")
            return
        if self.current_script() is None:
            script = fresh_script("Записанный сценарий")
            self.scripts.append(script)
            self.current_id = script["id"]
            self.save()
            self.open_editor()
        self.recorder.recording = not self.recorder.recording
        self.record_since = monotonic()
        if self.recorder.recording:
            self.statusBar().showMessage("● ЗАПИСЬ · F7 для завершения · вводимый текст не сохраняется")
            self.showMinimized()
        else:
            self.save()
            self.open_editor()
            self.showNormal()
            self.raise_()
            self.statusBar().showMessage("Запись остановлена. Проверьте полученные шаги.")

    def append_recorded_step(self, action, x=None, y=None, key=None):
        script = self.current_script()
        if not self.recorder.recording or not script:
            return
        if x is not None and not self.isMinimized() and self.geometry().contains(x, y):
            return
        step = fresh_step(action)
        if x is not None:
            step["region"] = {"x": x - 5, "y": y - 5, "w": 10, "h": 10}
        if key is not None:
            step["text"] = key
        if script["steps"]:
            script["steps"][-1]["delay_ms"] = min(120000, int((monotonic() - self.record_since) * 1000))
        step["delay_ms"] = 300
        self.record_since = monotonic()
        script["steps"].append(step)
        self.refresh_steps(step["id"])

    def on_recorded_click(self, x, y):
        self.append_recorded_step("click", x=x, y=y)

    def on_recorded_key(self, key):
        self.append_recorded_step("press_key", key=key)

    # ---- GitHub Releases -----------------------------------------------------
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
            answer = QMessageBox.question(self, "Обновление", f"{msg}. Открыть страницу релиза?")
            if answer == QMessageBox.Yes:
                self.open_release()

    def update_error(self, message, silent=False):
        self.update_status.setText("Не удалось проверить наличие обновлений")
        if not silent:
            QMessageBox.information(self, "Проверка обновлений", f"Ошибка соединения:\n{message}")

    def open_release(self):
        QDesktopServices.openUrl(QUrl(self.update_url or f"https://github.com/{GITHUB_REPOSITORY}/releases"))

    def closeEvent(self, event):
        if self.runner is not None and self.runner.isRunning():
            self.stop_runner()
            self.runner.wait(2500)
            if self.runner.isRunning():
                event.ignore()
                QMessageBox.warning(self, "Подождите", "Дождитесь остановки выполняемого действия.")
                return
        self.recorder.recording = False
        self.recorder.stop_listeners()
        self.save()
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyle("Fusion")
    fonts = QFontDatabase.families()
    font_name = next((f for f in FONT_PREFERENCES if f in fonts), "Segoe UI")
    font = QFont(font_name, 10)
    app.setFont(font)
    app.setWindowIcon(QIcon(str(asset_path("macroflow.ico"))))
    app.setStyleSheet(stylesheet(font_name))
    try:
        window = MainWindow()
    except RuntimeError as exc:
        QMessageBox.critical(None, "MacroFlow", str(exc))
        return 1
    window.show()
    return app.exec()
