"""MacroFlow visual primitives: real vector artwork, reusable interactive controls.

Icons are rendered from compact SVG geometry at runtime, not Unicode glyphs.
No external assets, fonts, or image downloads are required.
"""
from functools import lru_cache

from PySide6.QtCore import QByteArray, Qt, QSize, QRectF, QObject, QEvent, QTimer
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPixmap, QPen
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

ACCENT = '#FF8A24'
TEXT = '#EAF0F8'
MUTED = '#A6B3C4'

# Each icon uses a unified 24x24, 1.85px outlined vector geometry.
SHAPES = {
    'folder': '<path d="M3 7a2 2 0 0 1 2-2h5l2 2h7a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
    'bolt': '<path d="m13 2-9 11h7l-1 9 10-12h-7z"/>',
    'record': '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="4" fill="currentColor" stroke="none"/>',
    'layers': '<path d="m12 2 9 5-9 5-9-5zM3 12l9 5 9-5M3 17l9 5 9-5"/>',
    'settings': '<path d="M10 2h4l.8 2.7 2 1.1 2.7-.7 2 3.5-2 2 .1 2.3 2 2-2 3.5-2.7-.7-2 1.1L14 22h-4l-.8-2.7-2-1.1-2.7.7-2-3.5 2-2-.1-2.3-2-2 2-3.5 2.7.7 2-1.1z"/><circle cx="12" cy="12" r="3"/>',
    'cursor': '<path d="M4 3 4 20l5-5 3.2 6 3-1.7-3.1-6.1 7.5-.8z"/>',
    'keyboard': '<rect x="2" y="5" width="20" height="14" rx="2"/><path d="M6 9h.01M10 9h.01M14 9h.01M18 9h.01M6 12h.01M10 12h.01M14 12h.01M18 12h.01M7 16h10"/>',
    'clock': '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    'hourglass': '<path d="M6 3h12M6 21h12M7 3c0 5 1 6 5 9-4 3-5 4-5 9M17 3c0 5-1 6-5 9 4 3 5 4 5 9"/>',
    'text': '<path d="M4 5h16M12 5v15M7 20h10"/>',
    'search': '<circle cx="10.5" cy="10.5" r="6.5"/><path d="m15.5 15.5 5 5"/>',
    'window': '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18M6.5 6.5h.01M9.5 6.5h.01"/>',
    'target': '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1" fill="currentColor" stroke="none"/>',
    'scan': '<path d="M8 3H5a2 2 0 0 0-2 2v3m13-5h3a2 2 0 0 1 2 2v3M3 16v3a2 2 0 0 0 2 2h3m13-5v3a2 2 0 0 1-2 2h-3M6 12h12"/>',
    'play': '<path d="m7 4 13 8-13 8z" fill="currentColor" stroke="none"/>',
    'pause': '<rect x="6" y="4" width="4" height="16" rx="1" fill="currentColor" stroke="none"/><rect x="14" y="4" width="4" height="16" rx="1" fill="currentColor" stroke="none"/>',
    'stop': '<rect x="5" y="5" width="14" height="14" rx="2" fill="currentColor" stroke="none"/>',
    'step': '<path d="m4 4 11 8-11 8z" fill="currentColor" stroke="none"/><path d="M20 5v14"/>',
    'save': '<path d="M4 3h14l3 3v15H4zM7 3v7h10V3M7 21v-8h11v8"/>',
    'undo': '<path d="M9 7 4 12l5 5M4 12h11a5 5 0 0 1 0 10"/>',
    'redo': '<path d="m15 7 5 5-5 5m5-5H9a5 5 0 0 0 0 10"/>',
    'copy': '<rect x="8" y="8" width="12" height="13" rx="2"/><path d="M16 8V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h3"/>',
    'trash': '<path d="M4 7h16M9 7V4h6v3M6 7l1 14h10l1-14M10 11v7M14 11v7"/>',
    'plus': '<path d="M12 4v16M4 12h16"/>',
    'minus': '<path d="M4 12h16"/>',
    'up': '<path d="m5 14 7-7 7 7M12 7v14"/>',
    'down': '<path d="m5 10 7 7 7-7M12 17V3"/>',
    'chevron_down': '<path d="m6 9 6 6 6-6"/>',
    'chevron_right': '<path d="m9 5 7 7-7 7"/>',
    'menu': '<path d="M4 6h16M4 12h16M4 18h16"/>',
    'grid': '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
    'more': '<circle cx="5" cy="12" r="1.2" fill="currentColor" stroke="none"/><circle cx="12" cy="12" r="1.2" fill="currentColor" stroke="none"/><circle cx="19" cy="12" r="1.2" fill="currentColor" stroke="none"/>',
    'grip': '<circle cx="8" cy="5" r="1.2"/><circle cx="16" cy="5" r="1.2"/><circle cx="8" cy="12" r="1.2"/><circle cx="16" cy="12" r="1.2"/><circle cx="8" cy="19" r="1.2"/><circle cx="16" cy="19" r="1.2"/>',
    'check': '<path d="m4 12 5 5L20 6"/>',
    'info': '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7v.1"/>',
    'alert': '<path d="m12 3 10 18H2zM12 9v5M12 18v.1"/>',
    'file': '<path d="M6 2h9l5 5v15H6zM15 2v5h5M9 12h8M9 16h8"/>',
    'import': '<path d="M12 3v12m-5-5 5 5 5-5M4 17v4h16v-4"/>',
    'export': '<path d="M12 17V3m-5 5 5-5 5 5M4 17v4h16v-4"/>',
    'pencil': '<path d="M4 20h4l12-12-4-4L4 16zM14 6l4 4"/>',
    'maximize': '<rect x="5" y="5" width="14" height="14" rx="2"/>',
    'restore': '<path d="M8 8V4h12v12h-4M4 8h12v12H4z"/>',
    'close': '<path d="M5 5l14 14M19 5 5 19"/>',
    'line': '<path d="M4 12h16"/>',
    'external': '<path d="M13 4h7v7M20 4 10 14M20 14v6H4V4h6"/>',
    'refresh': '<path d="M20 7V3l-3 3A9 9 0 1 0 21 12M20 7h-6"/>',
    'shield': '<path d="M12 2 21 6v6c0 6-4 9-9 10-5-1-9-4-9-10V6zM8 12l3 3 5-6"/>',
    'power': '<path d="M12 2v10M5 5a9 9 0 1 0 14 0"/>',
    'sparkle': '<path d="m12 2 2 8 8 2-8 2-2 8-2-8-8-2 8-2z"/>',
}

@lru_cache(maxsize=512)
def vector_icon(name: str, color: str = TEXT, size: int = 24):
    shape = SHAPES.get(name, SHAPES['file']).replace('currentColor', color)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" '
           f'viewBox="0 0 24 24" fill="none" stroke="{color}" '
           f'color="{color}" stroke-width="1.85" stroke-linecap="round" '
           f'stroke-linejoin="round">{shape}</svg>')
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)
    QSvgRenderer(QByteArray(svg.encode('utf-8'))).render(painter)
    painter.end()
    return QIcon(pix)


def pictogram(name, color=ACCENT, size=22):
    lab = QLabel()
    lab.setObjectName('pictogram')
    lab.setPixmap(vector_icon(name, color, size).pixmap(size, size))
    lab.setFixedSize(size, size)
    lab.setAttribute(Qt.WA_TransparentForMouseEvents, True)
    return lab


class GraphicButton(QPushButton):
    """Vector-icon control with tactile hover / pressed visual feedback."""
    def __init__(self, text='', icon_name=None, on_click=None, role='secondary', icon_size=19, parent=None):
        super().__init__(text, parent)
        self._icon_name = icon_name
        self._role = role
        self._hovered = False
        self._pressed = False
        self.setObjectName(role)
        self.setProperty('visualRole', role)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(38 if role not in ('iconButton', 'titleButton', 'titleClose') else 32)
        if icon_name:
            self.setIconSize(QSize(icon_size, icon_size))
            self._update_icon()
        if on_click:
            self.clicked.connect(on_click)

    def _update_icon(self):
        if not self._icon_name:
            return
        if not self.isEnabled():
            col = '#677689'
        elif self._role == 'primary':
            col = '#15191F'
        elif self.isCheckable() and self.isChecked():
            col = ACCENT
        elif self._pressed:
            col = '#FFC183'
        elif self._hovered:
            col = '#FFFFFF'
        else:
            col = ACCENT if self._role == 'record' else TEXT
        self.setIcon(vector_icon(self._icon_name, col, self.iconSize().width()))

    def set_active(self, active):
        self.setChecked(active)
        self._update_icon()

    def enterEvent(self, event):
        self._hovered = True
        self._update_icon()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self._pressed = False
        self._update_icon()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        self._pressed = True
        self._update_icon()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self._pressed = False
        super().mouseReleaseEvent(event)
        self._update_icon()



class NavButton(GraphicButton):
    def __init__(self, text, icon_name, callback):
        super().__init__(text, icon_name, callback, role='navigation', icon_size=21)
        self.setCheckable(True)
        self.setMinimumHeight(49)
        self.setProperty('visualRole', 'navigation')


class TitleBar(QFrame):
    """Dark application-drawn titlebar; supports Windows drag and double-click maximize."""
    def __init__(self, parent, version, logo_path):
        super().__init__(parent)
        self.setObjectName('titleBar')
        self.setFixedHeight(43)
        row = QHBoxLayout(self)
        row.setContentsMargins(18, 3, 5, 3)
        row.setSpacing(9)
        logo = QLabel()
        logo.setObjectName('titleLogo')
        logo.setPixmap(QIcon(str(logo_path)).pixmap(23, 23))
        logo.setFixedSize(24, 24)
        row.addWidget(logo)
        title = QLabel(f'MacroFlow  —  Automation Studio')
        title.setObjectName('windowTitle')
        row.addWidget(title)
        version_label = QLabel(version)
        version_label.setObjectName('windowVersion')
        row.addWidget(version_label)
        row.addStretch(1)
        self.min_btn = GraphicButton('', 'line', parent.showMinimized, role='titleButton', icon_size=15)
        self.min_btn.setToolTip('Свернуть')
        row.addWidget(self.min_btn)
        self.max_btn = GraphicButton('', 'maximize', self.toggle_maximized, role='titleButton', icon_size=15)
        self.max_btn.setToolTip('Развернуть / восстановить')
        row.addWidget(self.max_btn)
        self.close_btn = GraphicButton('', 'close', parent.close, role='titleClose', icon_size=16)
        self.close_btn.setToolTip('Закрыть')
        row.addWidget(self.close_btn)
        self._drag = None

    def toggle_maximized(self):
        win = self.window()
        if win.isMaximized():
            win.showNormal()
            self.max_btn.setIcon(vector_icon('maximize', TEXT, 15))
        else:
            win.showMaximized()
            self.max_btn.setIcon(vector_icon('restore', TEXT, 15))

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.toggle_maximized()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and not self.window().isMaximized():
            handle = self.window().windowHandle()
            if handle and handle.startSystemMove():
                event.accept()
                return
            self._drag = event.globalPosition().toPoint() - self.window().frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag is not None and (event.buttons() & Qt.LeftButton):
            self.window().move(event.globalPosition().toPoint() - self._drag)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag = None
        super().mouseReleaseEvent(event)


class AccentWave(QWidget):
    """Subtle brand ribbon in sidebar - painted, not a Unicode character."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(28)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.moveTo(0, 20)
        path.cubicTo(self.width() * .3, 28, self.width() * .53, -2,
                     self.width(), 9)
        glow = QPen(QColor(255, 139, 43, 40), 10)
        painter.setPen(glow)
        painter.drawPath(path)
        painter.setPen(QPen(QColor(255, 139, 43, 225), 1.9))
        painter.drawPath(path)
        painter.end()


class WindowsDarkChrome(QObject):
    """Remove white native captions from standard Qt dialogs on supported Windows."""
    def eventFilter(self, obj, event):
        if (event.type() == QEvent.Show and isinstance(obj, QWidget)
                and obj.isWindow() and not (obj.windowFlags() & Qt.FramelessWindowHint)):
            QTimer.singleShot(0, lambda widget=obj: self._style_window(widget))
        return False

    @staticmethod
    def _style_window(widget):
        import sys
        if sys.platform != 'win32':
            return
        try:
            import ctypes
            hwnd = int(widget.winId())
            enabled = ctypes.c_int(1)
            # DWMWA_USE_IMMERSIVE_DARK_MODE on Windows 10 20H1+ and Windows 11.
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                ctypes.c_void_p(hwnd), 20, ctypes.byref(enabled), ctypes.sizeof(enabled))
        except (OSError, AttributeError, TypeError, ValueError, RuntimeError):
            pass  # A non-supporting Windows version still displays a usable dialog.
