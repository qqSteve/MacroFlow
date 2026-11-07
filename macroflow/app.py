"""MacroFlow — automation studio, custom 3.1 graphical interface.

All desktop interaction remains in the existing controller and engine.
The UI uses vector icons rendered from SVG and a reusable, accent-forward style.
"""
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
    QPlainTextEdit, QSizePolicy, QScrollArea,
)

from . import APP_NAME, __version__, GITHUB_REPOSITORY
from .theme import stylesheet, FONT_PREFERENCES, ACCENT, asset_path
from .visual import GraphicButton, NavButton, TitleBar, AccentWave, WindowsDarkChrome, vector_icon, pictogram
from .store import data_directory, fresh_script, fresh_step, load_scripts, save_scripts
from .exchange import parse_file, write_file
from .templates import TEMPLATES, build_template
from .engine import Runner, ACTIONS
from .recorder import Recorder
from .overlay import RegionSelector
from .updates import UpdateCheck

ACTION_ICONS = {
    'click': 'cursor', 'double_click': 'cursor', 'type_text': 'text',
    'press_key': 'keyboard', 'wait': 'hourglass', 'find_text': 'search',
}


def label(text, role=None, nowrap=False):
    result = QLabel(text)
    result.setTextFormat(Qt.PlainText)
    if role:
        result.setObjectName(role)
    result.setWordWrap(not nowrap)
    if nowrap:
        result.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    return result


def button(text, callback=None, primary=False, role=None, icon=None):
    return GraphicButton(text, icon, callback, role='primary' if primary else (role or 'secondary'))


def icon_button(icon, callback, tip='', role='iconButton', size=19):
    b = GraphicButton('', icon, callback, role=role, icon_size=size)
    b.setFixedWidth(42)
    if tip:
        b.setToolTip(tip)
    return b


def vbox(widget, margin=16, spacing=12):
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(margin, margin, margin, margin)
    layout.setSpacing(spacing)
    return layout


def panel(name='panel'):
    frame = QFrame()
    frame.setObjectName(name)
    return frame


def line_separator():
    line = QFrame()
    line.setObjectName('separator')
    line.setFixedHeight(1)
    return line


def section_header(icon, title, right=None):
    row = QHBoxLayout()
    row.setSpacing(10)
    row.addWidget(pictogram(icon, ACCENT, 22))
    row.addWidget(label(title, 'sectionTitle'))
    row.addStretch(1)
    if right is not None:
        row.addWidget(right)
    return row


def header_block(icon, title, desc, controls=None):
    head = QFrame()
    head.setObjectName('pageHeader')
    row = QHBoxLayout(head)
    row.setContentsMargins(0, 0, 0, 0)
    row.setSpacing(14)
    row.addWidget(pictogram(icon, ACCENT, 35))
    column = QVBoxLayout()
    column.setSpacing(3)
    column.addWidget(label(title, 'pageTitle', nowrap=True))
    column.addWidget(label(desc, 'pageSubtitle'))
    row.addLayout(column, 1)
    if controls is not None:
        row.addLayout(controls)
    return head


def field_label(text):
    return label(text, 'fieldLabel')


def spinbox(suffix=' мс', maximum=120000):
    w = QSpinBox()
    w.setRange(0, maximum)
    w.setSingleStep(50 if maximum > 10000 else 1)
    w.setSuffix(suffix)
    w.setMinimumWidth(102)
    w.setMinimumHeight(37)
    return w


def labeled_control(title, widget, min_width=None):
    c = QWidget()
    col = QVBoxLayout(c)
    col.setContentsMargins(0, 0, 0, 0)
    col.setSpacing(5)
    col.addWidget(field_label(title))
    col.addWidget(widget)
    if min_width:
        c.setMinimumWidth(min_width)
    return c


class StepListWidget(QListWidget):
    """A step card's vector ellipsis opens a real menu without harming drag/reorder."""
    def mousePressEvent(self, event):
        self._press_pos = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.position().toPoint()
            start = getattr(self, '_press_pos', pos)
            item = self.itemAt(pos)
            if item is not None and (pos - start).manhattanLength() < 8:
                right_edge = self.visualItemRect(item).right()
                if right_edge - 38 <= pos.x() <= right_edge:
                    self.setCurrentItem(item)
                    self.customContextMenuRequested.emit(pos)
                    event.accept()
                    return
        super().mouseReleaseEvent(event)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f'{APP_NAME} — Automation Studio {__version__}')
        self.setWindowIcon(QIcon(str(asset_path('macroflow.ico'))))
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowMinMaxButtonsHint)
        self.resize(1536, 900)
        self.setMinimumSize(1100, 730)
        self.scripts = load_scripts()
        self.current_id = None
        self.running_script_id = None
        self.runner = None
        self.checker = None
        self.update_url = None
        self.internal_change = False
        self.record_since = monotonic()
        self.steps_compact = False
        self.recorder = Recorder()
        self.recorder.shortcut.connect(self.on_hotkey)
        self.recorder.clicked.connect(self.on_recorded_click)
        self.recorder.pressed.connect(self.on_recorded_key)
        self.history = {}
        self.redo_history = {}
        self.history_latest = {s['id']: copy.deepcopy(s) for s in self.scripts}

        root = QWidget()
        root.setObjectName('appRoot')
        self.setCentralWidget(root)
        shell = QVBoxLayout(root)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)
        self.window_bar = TitleBar(self, __version__, asset_path('macroflow.ico'))
        shell.addWidget(self.window_bar)
        body = QWidget()
        body.setObjectName('body')
        shell.addWidget(body, 1)
        row = QHBoxLayout(body)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)
        self.make_nav(row)
        self.pages = QStackedWidget()
        row.addWidget(self.pages, 1)
        self.make_dashboard()    # 0
        self.make_editor()       # 1
        self.make_recording()    # 2
        self.make_tools()        # 3
        self.make_settings()     # 4
        self.show_page(0)
        self.refresh_scripts()
        self.statusBar().hide()  # No native white bar; status is custom sidebar footer.
        self.statusBar().showMessage('Готово · F6 запуск/пауза · F7 запись · F8 стоп · F9 шаг')
        if not self.recorder.start_listeners():
            QTimer.singleShot(0, lambda: QMessageBox.warning(
                self, 'Горячие клавиши',
                'Глобальные клавиши не запущены. Проверьте разрешения Windows.'))
        QTimer.singleShot(1800, self.check_updates_silent)

    def nativeEvent(self, event_type, message):
        """Keep all 8 Windows resize grips in the frameless window (6 px)."""
        if sys.platform == 'win32' and self.isVisible() and not self.isMaximized():
            try:
                import ctypes
                from ctypes import wintypes
                msg = wintypes.MSG.from_address(int(message))
                if msg.message == 0x0084:  # WM_NCHITTEST
                    x = ctypes.c_short(msg.lParam & 0xFFFF).value
                    y = ctypes.c_short((msg.lParam >> 16) & 0xFFFF).value
                    rect = wintypes.RECT()
                    ctypes.windll.user32.GetWindowRect(msg.hwnd, ctypes.byref(rect))
                    gap = 7
                    left, right = x < rect.left + gap, x >= rect.right - gap
                    top, bottom = y < rect.top + gap, y >= rect.bottom - gap
                    if top and left: return True, 13  # HTTOPLEFT
                    if top and right: return True, 14
                    if bottom and left: return True, 16
                    if bottom and right: return True, 17
                    if left: return True, 10
                    if right: return True, 11
                    if top: return True, 12
                    if bottom: return True, 15
            except Exception:
                pass
        return super().nativeEvent(event_type, message)

    def make_nav(self, root):
        sidebar = QFrame()
        sidebar.setObjectName('sidebar')
        sidebar.setFixedWidth(290)
        layout = vbox(sidebar, 17, 7)
        brand = QFrame()
        brand.setObjectName('brandArea')
        brandrow = QHBoxLayout(brand)
        brandrow.setContentsMargins(8, 9, 3, 5)
        brandrow.setSpacing(13)
        app_icon = QLabel()
        app_icon.setPixmap(QIcon(str(asset_path('macroflow.ico'))).pixmap(70, 70))
        app_icon.setFixedSize(72, 72)
        brandrow.addWidget(app_icon)
        brandtext = QVBoxLayout()
        brandtext.setSpacing(1)
        brandtext.addWidget(label('MACROFLOW', 'brandTitle'))
        brandtext.addWidget(label('AUTOMATION STUDIO', 'brandSubtitle'))
        brandrow.addLayout(brandtext)
        layout.addWidget(brand)
        layout.addWidget(AccentWave())
        layout.addSpacing(12)
        layout.addWidget(label('НАВИГАЦИЯ', 'navSection'))
        layout.addSpacing(6)
        self.nav_buttons = []
        items = [('Мои сценарии', 'folder'), ('Редактор макросов', 'bolt'),
                 ('Запись действий', 'record'), ('Инструменты', 'layers'),
                 ('Настройки', 'settings')]
        for i, (title, ico) in enumerate(items):
            nav = NavButton(title, ico, partial(self.show_page, i))
            layout.addWidget(nav)
            self.nav_buttons.append(nav)
        layout.addSpacing(14)
        layout.addWidget(line_separator())
        layout.addSpacing(10)
        layout.addWidget(label('БЫСТРЫЙ ДОСТУП', 'navSection'))
        layout.addSpacing(4)
        shortcuts = [
            ('Записать сценарий', 'record', self.toggle_record),
            ('Захват области', 'scan', self.pick_region),
            ('Импорт сценария', 'import', self.import_scripts),
            ('Экспорт сценариев', 'export', self.export_all_scripts),
        ]
        for text, ico, handler in shortcuts:
            layout.addWidget(button(text, handler, role='quickAction', icon=ico))
        layout.addStretch(1)
        layout.addWidget(line_separator())
        layout.addSpacing(9)
        for key, desc in [('F6', 'Запуск / пауза'), ('F7', 'Запись действий'),
                          ('F8', 'Остановить'), ('F9', 'Один шаг')]:
            hot = QWidget()
            hotrow = QHBoxLayout(hot)
            hotrow.setContentsMargins(0, 1, 0, 1)
            hotrow.setSpacing(10)
            keycap = label(key, 'keycap')
            keycap.setFixedWidth(39)
            keycap.setAlignment(Qt.AlignCenter)
            hotrow.addWidget(keycap)
            hotrow.addWidget(label(desc, 'shortcutHint'))
            layout.addWidget(hot)
        layout.addStretch(1)
        footer = QFrame()
        footer.setObjectName('sidebarFooter')
        frow = QHBoxLayout(footer)
        frow.setContentsMargins(4, 6, 4, 5)
        self.state_indicator = label('●', 'accent')
        self.state_indicator.setStyleSheet('color:#22C666;font-size:17px;')
        frow.addWidget(self.state_indicator)
        self.sidebar_status = label('Готово к работе', 'sidebarStatus')
        frow.addWidget(self.sidebar_status, 1)
        layout.addWidget(footer)
        root.addWidget(sidebar)

    def show_page(self, index):
        self.pages.setCurrentIndex(index)
        for i, nav in enumerate(self.nav_buttons):
            nav.set_active(i == index)

    def make_dashboard(self):
        page = QWidget()
        layout = vbox(page, 24, 15)
        toolbar = QHBoxLayout()
        toolbar.setSpacing(9)
        toolbar.addWidget(button('Новый сценарий', self.new_script, True, icon='plus'))
        toolbar.addWidget(button('Из шаблона', self.new_from_template, icon='layers'))
        toolbar.addWidget(button('Импорт .mflow', self.import_scripts, icon='import'))
        toolbar.addWidget(button('Экспорт всех', self.export_all_scripts, icon='export'))
        toolbar.addStretch()
        layout.addWidget(header_block('folder', 'Мои сценарии',
                    'Библиотека сценариев — создание, запуск и обмен макросами.'))
        layout.addLayout(toolbar)
        holder = panel('workPanel')
        body = vbox(holder, 17, 10)
        self.dashboard_count = label('0', 'countPill')
        body.addLayout(section_header('folder', 'Библиотека сценариев', self.dashboard_count))
        self.script_list = QListWidget()
        self.script_list.setObjectName('scenarioList')
        self.script_list.setSpacing(3)
        self.script_list.itemDoubleClicked.connect(self.open_selected_script)
        self.script_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.script_list.customContextMenuRequested.connect(self.show_script_menu)
        body.addWidget(self.script_list, 1)
        body.addWidget(label('Двойной клик — открыть. Правый клик — изменить, копировать, экспортировать или удалить.', 'muted'))
        layout.addWidget(holder, 1)
        self.pages.addWidget(page)

    def make_editor(self):
        page = QWidget()
        layout = vbox(page, 19, 10)
        tools = QHBoxLayout()
        tools.setSpacing(8)
        self.undo_btn = icon_button('undo', self.undo_change, 'Отменить последнее изменение')
        self.redo_btn = icon_button('redo', self.redo_change, 'Повторить изменение')
        tools.addWidget(self.undo_btn)
        tools.addWidget(self.redo_btn)
        tools.addWidget(icon_button('copy', self.duplicate_step, 'Копировать действие'))
        tools.addWidget(icon_button('trash', self.delete_step, 'Удалить действие'))
        tools.addSpacing(11)
        tools.addWidget(button('Сохранить сценарий', self.save, True, icon='save'))
        layout.addWidget(header_block('bolt', 'Редактор макросов',
                                    'Создание и настройка сценария автоматизации', tools))
        ident = panel('parameterPanel')
        ident_row = QHBoxLayout(ident)
        ident_row.setContentsMargins(11, 9, 11, 9)
        ident_row.setSpacing(10)
        ident_row.addWidget(pictogram('file', '#AAB6C7', 21))
        self.script_name = QLineEdit()
        self.script_name.setPlaceholderText('Название сценария')
        self.script_name.editingFinished.connect(self.rename_current)
        ident_row.addWidget(self.script_name, 2)
        ident_row.addSpacing(10)
        ident_row.addWidget(pictogram('pencil', '#AAB6C7', 19))
        self.script_description = QLineEdit()
        self.script_description.setPlaceholderText('Описание сценария (необязательно)')
        self.script_description.editingFinished.connect(self.describe_current)
        ident_row.addWidget(self.script_description, 3)
        layout.addWidget(ident)

        opts = panel('parameterPanel')
        op = vbox(opts, 13, 10)
        op.addLayout(section_header('play', 'Запуск и повторения'))
        fields = QHBoxLayout()
        fields.setSpacing(15)
        self.repeat_mode = QComboBox()
        self.repeat_mode.addItem('Один раз', 'once')
        self.repeat_mode.addItem('Заданное количество', 'count')
        self.repeat_mode.addItem('Бесконечно', 'forever')
        self.repeat_mode.currentIndexChanged.connect(self.apply_repeat_settings)
        fields.addWidget(labeled_control('Режим повтора', self.repeat_mode, 164), 2)
        self.repeat_count = spinbox('', 1000000)
        self.repeat_count.setMinimum(1)
        self.repeat_count.valueChanged.connect(self.apply_repeat_settings)
        fields.addWidget(labeled_control('Количество циклов', self.repeat_count, 112), 1)
        self.cycle_delay = spinbox(' мс')
        self.cycle_delay.valueChanged.connect(self.apply_repeat_settings)
        fields.addWidget(labeled_control('Пауза между циклами', self.cycle_delay, 137), 1)
        self.global_delay = spinbox(' мс')
        self.global_delay.valueChanged.connect(self.apply_repeat_settings)
        fields.addWidget(labeled_control('Общая задержка', self.global_delay, 126), 1)
        op.addLayout(fields)
        layout.addWidget(opts)

        self.edit_split = QSplitter(Qt.Horizontal)
        self.edit_split.setChildrenCollapsible(False)
        self.edit_split.setHandleWidth(10)
        left = panel('workPanel')
        ll = vbox(left, 13, 10)
        viewbar = QHBoxLayout()
        viewbar.setSpacing(8)
        viewbar.addWidget(pictogram('layers', ACCENT, 22))
        viewbar.addWidget(label('Последовательность действий', 'sectionTitle'))
        self.step_count = label('0', 'countPill')
        viewbar.addWidget(self.step_count)
        viewbar.addStretch()
        self.list_mode_btn = icon_button('menu', lambda: self.change_step_display(False), 'Подробный список')
        self.compact_mode_btn = icon_button('grid', lambda: self.change_step_display(True), 'Компактный список')
        self.list_mode_btn.setCheckable(True)
        self.compact_mode_btn.setCheckable(True)
        self.list_mode_btn.setChecked(True)
        viewbar.addWidget(self.list_mode_btn)
        viewbar.addWidget(self.compact_mode_btn)
        ll.addLayout(viewbar)
        self.step_list = StepListWidget()
        self.step_list.setObjectName('stepsList')
        self.step_list.setSpacing(2)
        self.step_list.setDragDropMode(QAbstractItemView.InternalMove)
        self.step_list.setDefaultDropAction(Qt.MoveAction)
        self.step_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.step_list.itemSelectionChanged.connect(self.select_step)
        self.step_list.model().rowsMoved.connect(self.reordered_steps)
        self.step_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.step_list.customContextMenuRequested.connect(self.show_step_menu)
        ll.addWidget(self.step_list, 1)
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        add = button('Добавить действие', self.show_add_action_menu, True, icon='plus')
        toolbar.addWidget(add, 1)
        toolbar.addWidget(icon_button('up', partial(self.shift_step, -1), 'Вверх'))
        toolbar.addWidget(icon_button('down', partial(self.shift_step, 1), 'Вниз'))
        toolbar.addWidget(icon_button('copy', self.duplicate_step, 'Копировать'))
        toolbar.addWidget(icon_button('trash', self.delete_step, 'Удалить'))
        ll.addLayout(toolbar)
        self.edit_split.addWidget(left)

        right = panel('inspectorPanel')
        rl = vbox(right, 15, 13)
        self.inspector_badge = label('Выберите действие', 'countPill')
        rl.addLayout(section_header('settings', 'Настройки действия', self.inspector_badge))
        heading = panel('inspectorHeading')
        hrow = QHBoxLayout(heading)
        hrow.setContentsMargins(12, 11, 12, 11)
        icon_shell = panel('actionIconBox')
        icon_shell.setFixedSize(52, 52)
        icon_shell_row = QHBoxLayout(icon_shell)
        icon_shell_row.setContentsMargins(8, 8, 8, 8)
        self.inspector_icon = pictogram('cursor', ACCENT, 33)
        icon_shell_row.addWidget(self.inspector_icon)
        hrow.addWidget(icon_shell)
        hcol = QVBoxLayout()
        hcol.setSpacing(3)
        self.inspector_title = label('Выбери шаг слева', 'actionHeading')
        self.inspector_description = label('Параметры появятся здесь', 'actionDetails')
        hcol.addWidget(self.inspector_title)
        hcol.addWidget(self.inspector_description)
        hrow.addLayout(hcol, 1)
        rl.addWidget(heading)
        self.action_field = QComboBox()
        for key, title in ACTIONS.items():
            self.action_field.addItem(title, key)
        self.action_field.currentIndexChanged.connect(self.apply_step_edits)
        rl.addWidget(labeled_control('Тип действия', self.action_field))
        self.delay_field = spinbox(' мс')
        self.delay_field.valueChanged.connect(self.apply_step_edits)
        rl.addWidget(labeled_control('Задержка после действия', self.delay_field))
        self.text_field_group = QWidget()
        tf = QVBoxLayout(self.text_field_group)
        tf.setContentsMargins(0, 0, 0, 0)
        tf.setSpacing(5)
        tf.addWidget(field_label('Текст / клавиша'))
        self.text_field = QLineEdit()
        self.text_field.setPlaceholderText('Например, enter или значение')
        self.text_field.editingFinished.connect(self.apply_step_edits)
        tf.addWidget(self.text_field)
        rl.addWidget(self.text_field_group)
        self.enabled_field = QCheckBox('Выполнять действие')
        self.enabled_field.stateChanged.connect(self.apply_step_edits)
        rl.addWidget(self.enabled_field)
        self.region_label = label('Область не выбрана', 'muted')
        rl.addWidget(self.region_label)
        self.pick_region_btn = button('Выделить область на экране', self.pick_region, icon='scan')
        rl.addWidget(self.pick_region_btn)
        rl.addWidget(line_separator())
        rl.addWidget(field_label('Быстрая установка задержки'))
        presets = QHBoxLayout()
        presets.setSpacing(5)
        for ms in (100, 300, 600, 1000, 3000):
            b = button(f'{ms:,} мс'.replace(',', ' '), partial(self.set_delay_preset, ms))
            b.setToolTip('Установить задержку после выбранного действия')
            presets.addWidget(b)
        rl.addLayout(presets)
        helpcard = panel('helpCard')
        helpbox = vbox(helpcard, 12, 7)
        helpbox.addLayout(section_header('info', 'Подсказка'))
        self.step_help = label('Выберите действие для редактирования. Любое изменение сохраняется локально.', 'hint')
        helpbox.addWidget(self.step_help)
        rl.addWidget(helpcard)
        rl.addStretch(1)
        self.edit_split.addWidget(right)
        self.edit_split.setStretchFactor(0, 12)
        self.edit_split.setStretchFactor(1, 9)
        self.edit_split.setSizes([750, 520])
        layout.addWidget(self.edit_split, 1)

        transport = panel('transportPanel')
        ct = QHBoxLayout(transport)
        ct.setContentsMargins(10, 9, 10, 9)
        ct.setSpacing(9)
        self.play_button = button('Старт / Пауза    F6', self.start_or_pause, True, icon='play')
        ct.addWidget(self.play_button, 2)
        self.record_button = button('Запись    F7', self.toggle_record, role='record', icon='record')
        self.record_button.setCheckable(True)
        ct.addWidget(self.record_button, 1)
        ct.addWidget(button('Стоп    F8', self.stop_runner, role='danger', icon='stop'), 1)
        ct.addWidget(button('Один шаг    F9', self.run_one, icon='step'), 1)
        self.toggle_log_btn = button('Журнал', self.toggle_log, icon='menu')
        ct.addWidget(self.toggle_log_btn, 1)
        layout.addWidget(transport)
        self.log_panel = panel('logPanel')
        loglayout = vbox(self.log_panel, 13, 6)
        loghead = QHBoxLayout()
        loghead.addWidget(pictogram('menu', ACCENT, 18))
        loghead.addWidget(label('Журнал', 'sectionTitle'))
        loghead.addStretch()
        loghead.addWidget(button('Очистить', self.clear_log, icon='trash'))
        loglayout.addLayout(loghead)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(400)
        self.log.setPlainText('Ожидание запуска сценария…')
        self.log.setFixedHeight(77)
        loglayout.addWidget(self.log)
        layout.addWidget(self.log_panel)
        self.pages.addWidget(page)

    def make_recording(self):
        page = QWidget()
        layout = vbox(page, 25, 17)
        layout.addWidget(header_block('record', 'Запись действий',
                         'Записывай клики мыши и служебные клавиши, превращай их в редактируемые шаги.'))
        intro = panel('workPanel')
        col = vbox(intro, 21, 16)
        col.addLayout(section_header('record', 'Рекордер MacroFlow'))
        col.addWidget(label('Нажми «Начать запись» или F7, затем выполняй действия в другой программе. '
                            'Повторное нажатие F7 остановит запись, после чего откроется редактор.', 'hint'))
        col.addWidget(button('Начать / остановить запись    F7', self.toggle_record, True, icon='record'))
        col.addWidget(line_separator())
        col.addLayout(section_header('shield', 'Приватность и безопасность'))
        col.addWidget(label('Рекордер фиксирует координаты кликов и отдельные служебные клавиши. '
                            'Обычный ввод текста и пароли не записываются. Запись запускается только вручную.', 'hint'))
        col.addWidget(label('Перед массовым запуском проверь каждый созданный шаг в редакторе.', 'muted'))
        layout.addWidget(intro)
        layout.addStretch(1)
        self.pages.addWidget(page)

    def make_tools(self):
        page = QWidget()
        layout = vbox(page, 25, 16)
        layout.addWidget(header_block('layers', 'Инструменты',
                                     'Быстрый доступ к библиотеке действий и обмену сценариями.'))
        card = panel('workPanel')
        col = vbox(card, 18, 13)
        col.addLayout(section_header('plus', 'Библиотека действий'))
        col.addWidget(label('Выбери действие — оно добавится в открытый сценарий.', 'muted'))
        tools = [('Левый клик', 'cursor', 'click'), ('Двойной клик', 'cursor', 'double_click'),
                 ('Ввод текста', 'text', 'type_text'), ('Нажать клавишу', 'keyboard', 'press_key'),
                 ('Ожидание', 'hourglass', 'wait')]
        for i in range(0, len(tools), 2):
            line = QHBoxLayout()
            line.setSpacing(10)
            for title, ico, action in tools[i:i+2]:
                line.addWidget(button(title, partial(self.add_specific_step, action), icon=ico), 1)
            if len(tools[i:i+2]) == 1:
                line.addStretch(1)
            col.addLayout(line)
        col.addWidget(line_separator())
        col.addLayout(section_header('import', 'Обмен сценариями'))
        row = QHBoxLayout()
        row.addWidget(button('Импорт .mflow', self.import_scripts, icon='import'))
        row.addWidget(button('Экспорт всех', self.export_all_scripts, icon='export'))
        row.addStretch()
        col.addLayout(row)
        col.addWidget(label('Поиск текста и элементов окна появится в следующем функциональном обновлении. '
                            'Пока эти инструменты не выполняют поиск в 1С.', 'muted'))
        layout.addWidget(card)
        layout.addStretch(1)
        self.pages.addWidget(page)

    def make_settings(self):
        page = QWidget()
        layout = vbox(page, 25, 13)
        layout.addWidget(header_block('settings', 'Настройки',
                    'Параметры приложения, обновления и управление рабочим столом.'))
        update = panel('workPanel')
        u = vbox(update, 18, 12)
        u.addLayout(section_header('refresh', 'Обновления через GitHub'))
        u.addWidget(label(f'Репозиторий: {GITHUB_REPOSITORY}    •    Текущая версия: {__version__}', 'hint'))
        self.update_status = label('Проверка обновлений ещё не выполнена', 'muted')
        u.addWidget(self.update_status)
        row = QHBoxLayout()
        row.addWidget(button('Проверить обновления', partial(self.check_updates, False), True, icon='refresh'))
        row.addWidget(button('Открыть релизы', self.open_release, icon='external'))
        row.addStretch()
        u.addLayout(row)
        layout.addWidget(update)
        kb = panel('workPanel')
        k = vbox(kb, 18, 12)
        k.addLayout(section_header('keyboard', 'Глобальные горячие клавиши'))
        k.addWidget(label('F6 — запуск / пауза     •     F7 — запись     •     F8 — стоп     •     F9 — один шаг', 'hint'))
        k.addWidget(label('Горячие клавиши работают при свёрнутом окне. Переназначение будет добавлено позже.', 'muted'))
        layout.addWidget(kb)
        security = panel('workPanel')
        sec = vbox(security, 18, 12)
        sec.addLayout(section_header('shield', 'Безопасность автоматизации'))
        sec.addWidget(label('Сценарии хранятся только на компьютере. Импортированные сценарии не запускаются автоматически.', 'hint'))
        sec.addWidget(label('В 1С сначала проверяйте действия на тестовых документах. Для бесконечного повтора требуется подтверждение.', 'muted'))
        layout.addWidget(security)
        layout.addStretch(1)
        self.pages.addWidget(page)

    def change_step_display(self, compact):
        self.steps_compact = compact
        self.list_mode_btn.setChecked(not compact)
        self.compact_mode_btn.setChecked(compact)
        step = self.current_step()
        self.refresh_steps(step['id'] if step else None)

    def show_add_action_menu(self):
        menu = QMenu(self)
        for action, title in ACTIONS.items():
            if action == 'find_text':
                continue  # The engine does not support it yet.
            item = menu.addAction(vector_icon(ACTION_ICONS.get(action, 'file'), ACCENT, 18), title)
            item.triggered.connect(lambda checked=False, chosen=action: self.add_specific_step(chosen))
        menu.exec(self.cursor().pos())

    def add_specific_step(self, action):
        if self.current_script() is None:
            self.new_script()
        script = self.current_script()
        if script is None:
            return
        step = fresh_step(action)
        script['steps'].append(step)
        self.refresh_steps(step['id'])
        self.save()
        self.show_page(1)

    def show_step_menu(self, pos):
        item = self.step_list.itemAt(pos)
        if item is None:
            return
        self.step_list.setCurrentItem(item)
        menu = QMenu(self)
        dup = menu.addAction(vector_icon('copy', ACCENT), 'Копировать действие')
        up = menu.addAction(vector_icon('up', ACCENT), 'Вверх')
        down = menu.addAction(vector_icon('down', ACCENT), 'Вниз')
        menu.addSeparator()
        delete = menu.addAction(vector_icon('trash', '#FC8392'), 'Удалить действие')
        chosen = menu.exec(self.step_list.viewport().mapToGlobal(pos))
        if chosen is dup: self.duplicate_step()
        elif chosen is up: self.shift_step(-1)
        elif chosen is down: self.shift_step(1)
        elif chosen is delete: self.delete_step()

    def set_delay_preset(self, ms):
        if self.current_step():
            self.delay_field.setValue(ms)

    def toggle_log(self):
        self.log_panel.setVisible(not self.log_panel.isVisible())

    def clear_log(self):
        self.log.clear()

    def add_log(self, message):
        when = datetime.now().strftime('%H:%M:%S')
        self.log.appendPlainText(f'{when}   {message}')
        self.sidebar_status.setText(str(message)[:38])

    def undo_change(self):
        script = self.current_script()
        if not script or not self.history.get(script['id']):
            return
        sid = script['id']
        self.redo_history.setdefault(sid, []).append(copy.deepcopy(script))
        previous = self.history[sid].pop()
        self._restore_history_snapshot(sid, previous)

    def redo_change(self):
        script = self.current_script()
        if not script or not self.redo_history.get(script['id']):
            return
        sid = script['id']
        self.history.setdefault(sid, []).append(copy.deepcopy(script))
        next_state = self.redo_history[sid].pop()
        self._restore_history_snapshot(sid, next_state)

    def _restore_history_snapshot(self, sid, state):
        for i, sc in enumerate(self.scripts):
            if sc['id'] == sid:
                self.scripts[i] = copy.deepcopy(state)
                break
        self.history_latest[sid] = copy.deepcopy(state)
        save_scripts(self.scripts)
        self.open_editor()
        self.refresh_scripts()
        self._refresh_history_buttons()
        self.add_log('История изменений обновлена')

    def _refresh_history_buttons(self):
        sid = self.current_id
        self.undo_btn.setEnabled(bool(self.history.get(sid)))
        self.redo_btn.setEnabled(bool(self.redo_history.get(sid)))

    # ---- Scenario library and .mflow interchange -----------------------------
    def refresh_scripts(self):
        selected = self.current_id
        self.script_list.clear()
        self.dashboard_count.setText(str(len(self.scripts)))
        for script in self.scripts:
            item = QListWidgetItem()
            item.setData(Qt.UserRole, script['id'])
            item.setSizeHint(QSize(160, 79))
            self.script_list.addItem(item)
            entry = QWidget()
            entry.setObjectName('scenarioContents')
            entry.setAttribute(Qt.WA_TransparentForMouseEvents, True)
            row = QHBoxLayout(entry)
            row.setContentsMargins(16, 7, 16, 7)
            row.setSpacing(15)
            row.addWidget(pictogram('file', ACCENT, 25))
            info = QVBoxLayout()
            info.setSpacing(5)
            title = label(script.get('name', 'Без названия'), 'scenarioTitle', nowrap=True)
            info.addWidget(title)
            description = script.get('description') or 'Двойной клик — открыть сценарий'
            changed = script.get('updated_at')
            if changed:
                try:
                    description += '   •   ' + datetime.fromisoformat(changed).strftime('%d.%m.%Y')
                except ValueError:
                    pass
            subtitle = label(description, 'scenarioSubtitle', nowrap=True)
            info.addWidget(subtitle)
            row.addLayout(info, 1)
            row.addWidget(pictogram('chevron_right', '#9EACBC', 19))
            self.script_list.setItemWidget(item, entry)
            if script['id'] == selected:
                self.script_list.setCurrentItem(item)

    def current_script(self):
        return next((s for s in self.scripts if s["id"] == self.current_id), None)

    def save(self):
        script = self.current_script()
        if script:
            sid = script['id']
            previous = self.history_latest.get(sid)
            # No history entry when the scenario did not change.
            if previous is not None:
                current = {k: v for k, v in script.items() if k != 'updated_at'}
                prior = {k: v for k, v in previous.items() if k != 'updated_at'}
                if current != prior:
                    stack = self.history.setdefault(sid, [])
                    stack.append(copy.deepcopy(previous))
                    if len(stack) > 60:
                        del stack[:-60]
                    self.redo_history[sid] = []
            script['updated_at'] = datetime.now().astimezone().isoformat(timespec='seconds')
            self.history_latest[sid] = copy.deepcopy(script)
        save_scripts(self.scripts)
        self.refresh_scripts()
        self._refresh_history_buttons()
        self.statusBar().showMessage('Изменения сохранены')

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
        edit_action = menu.addAction(vector_icon('pencil', ACCENT, 18), 'Изменить')
        rename_action = menu.addAction(vector_icon('pencil', ACCENT, 18), 'Переименовать')
        copy_action = menu.addAction(vector_icon('copy', ACCENT, 18), 'Копировать')
        export_action = menu.addAction(vector_icon('export', ACCENT, 18), 'Экспортировать .mflow')
        menu.addSeparator()
        folder_action = menu.addAction(vector_icon('folder', ACCENT, 18), 'Показать папку сценариев')
        delete_action = menu.addAction(vector_icon('trash', '#F68F98', 18), 'Удалить')
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
        self._refresh_history_buttons()
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
        if select_id is None and self.step_list.currentItem():
            select_id = self.step_list.currentItem().data(Qt.UserRole)
        self.step_list.clear()
        steps = script.get('steps', []) if script else []
        self.step_count.setText(str(len(steps)))
        for number, step in enumerate(steps, 1):
            title = ACTIONS.get(step['action'], step['action'])
            action = step.get('action', 'click')
            icon = ACTION_ICONS.get(action, 'file')
            item = QListWidgetItem()
            item.setData(Qt.UserRole, step['id'])
            item.setSizeHint(QSize(220, 44 if self.steps_compact else 62))
            self.step_list.addItem(item)
            entry = QWidget()
            entry.setObjectName('stepContents')
            entry.setAttribute(Qt.WA_TransparentForMouseEvents, True)
            row = QHBoxLayout(entry)
            row.setContentsMargins(10, 2, 10, 2)
            row.setSpacing(11)
            row.addWidget(pictogram('grip', '#738194', 18))
            no = label(str(number), 'stepIndex')
            no.setAlignment(Qt.AlignCenter)
            no.setFixedWidth(22)
            row.addWidget(no)
            icon_shell = panel('stepIconBox')
            icon_shell.setFixedSize(40, 40) if not self.steps_compact else icon_shell.setFixedSize(32, 32)
            iconrow = QHBoxLayout(icon_shell)
            iconrow.setContentsMargins(5, 5, 5, 5)
            iconrow.addWidget(pictogram(icon, ACCENT if step.get('enabled', True) else '#79889B',
                                        23 if not self.steps_compact else 19))
            row.addWidget(icon_shell)
            body = QVBoxLayout()
            body.setSpacing(2)
            body.addWidget(label(title, 'stepTitle', nowrap=True))
            if not self.steps_compact:
                extra = step.get('text', '') if action in ('press_key', 'type_text') else ''
                if action in ('click', 'double_click'):
                    region = step.get('region')
                    extra = 'Область не задана' if not region else f"X: {region['x']}   Y: {region['y']}"
                if action == 'wait':
                    extra = 'Пауза между действиями'
                if not step.get('enabled', True):
                    extra = 'Отключено • ' + extra
                body.addWidget(label(str(extra)[:80], 'stepDetails', nowrap=True))
            row.addLayout(body, 1)
            delay = label(f"{step.get('delay_ms', 0)} мс", 'stepDelay')
            delay.setAlignment(Qt.AlignCenter)
            row.addWidget(delay)
            row.addWidget(pictogram('more', '#9CA9BA', 18))
            self.step_list.setItemWidget(item, entry)
            if select_id == step['id']:
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
        self.pick_region_btn.setEnabled(step is not None)
        if step:
            action = step['action']
            index = self.action_field.findData(action)
            self.action_field.setCurrentIndex(max(0, index))
            self.delay_field.setValue(int(step.get('delay_ms', 300)))
            self.text_field.setText(step.get('text', ''))
            self.enabled_field.setChecked(step.get('enabled', True))
            self.region_label.setText(
                f"Область: {step['region']}" if step.get('region') else 'Область не выбрана')
            self.inspector_badge.setText(f'#{self.step_list.currentRow()+1}')
            self.inspector_title.setText(ACTIONS.get(action, action))
            help_by_type = {
                'click': 'Выдели область кнопки; клик выполняется по её центру.',
                'double_click': 'Двойной клик по центру выбранной области.',
                'type_text': 'Введите текст латиницей. Кириллица в этом движке пока не поддерживается.',
                'press_key': 'Укажи клавишу в поле (например, enter, tab или esc).',
                'wait': 'Это действие ждёт заданную задержку, затем переходит дальше.',
                'find_text': 'Поиск текста пока не реализован. Не запускай этот шаг.',
            }
            desc = help_by_type.get(action, 'Настрой параметры выбранного действия.')
            self.inspector_description.setText('Редактирование выбранного шага')
            self.step_help.setText(desc)
            self.inspector_icon.setPixmap(vector_icon(
                ACTION_ICONS.get(action, 'file'), ACCENT, 33).pixmap(33, 33))
            self.text_field_group.setVisible(action in ('type_text', 'press_key', 'find_text'))
            self.region_label.setVisible(action in ('click', 'double_click'))
            self.pick_region_btn.setVisible(action in ('click', 'double_click'))
            if action == 'find_text':
                self.step_help.setText('Поиск текста ещё не работает в движке. Действие недоступно для выполнения.')
        else:
            self.inspector_badge.setText('Нет шага')
            self.inspector_title.setText('Выберите действие')
            self.inspector_description.setText('Параметры появятся здесь')
            self.region_label.setText('Выберите действие слева')
            self.step_help.setText('Добавьте действие или выберите существующее для редактирования.')
            self.text_field_group.hide()
            self.region_label.hide()
            self.pick_region_btn.hide()
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
            QMessageBox.information(self, 'Захват области',
                'Сначала откройте редактор, создайте действие «Клик» и выберите его.')
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
        self.add_log(message)
        self.statusBar().showMessage(message)

    def runner_finished(self):
        runner = self.runner
        self.runner = None
        self.running_script_id = None
        if runner:
            runner.deleteLater()

    def show_running_step(self, index):
        self.statusBar().showMessage(f"Выполняется шаг {index+1}")
        self.sidebar_status.setText(f"Выполняется шаг {index+1}")
        if self.current_id == self.running_script_id and self.pages.currentIndex() == 1:
            if 0 <= index < self.step_list.count():
                self.step_list.setCurrentRow(index)

    def update_cycle_progress(self, completed, total):
        suffix = str(total) if total else "∞"
        self.statusBar().showMessage(f"Сценарий: завершено циклов {completed}/{suffix}")
        self.sidebar_status.setText(f"Циклов: {completed}/{suffix}")

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
        self.runner.log.connect(self.add_log)
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
        self.record_button.setChecked(self.recorder.recording)
        self.record_since = monotonic()
        if self.recorder.recording:
            self.statusBar().showMessage("ЗАПИСЬ · F7 для завершения · вводимый текст не сохраняется")
            self.sidebar_status.setText("Идёт запись")
            self.showMinimized()
        else:
            self.sidebar_status.setText("Готово к работе")
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
    dark_chrome = WindowsDarkChrome(app)
    app.installEventFilter(dark_chrome)
    try:
        window = MainWindow()
    except RuntimeError as exc:
        QMessageBox.critical(None, "MacroFlow", str(exc))
        return 1
    window.show()
    return app.exec()
