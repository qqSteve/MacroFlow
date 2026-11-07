from PySide6.QtCore import Qt, QRect, QPoint
from PySide6.QtGui import QColor, QPainter, QPen, QGuiApplication
from PySide6.QtWidgets import QDialog


class RegionSelector(QDialog):
    """Click-and-drag on the screen to choose a rectangular target area."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setCursor(Qt.CrossCursor)
        self.setMouseTracking(True)
        self.setGeometry(QGuiApplication.primaryScreen().virtualGeometry())
        self.start_pos = None
        self.end_pos = None
        self.region = None

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self.reject()
            return
        self.start_pos = event.position().toPoint()
        self.end_pos = self.start_pos
        self.update()

    def mouseMoveEvent(self, event):
        if self.start_pos is not None:
            self.end_pos = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event):
        if not self.start_pos or event.button() != Qt.LeftButton:
            return
        rect = QRect(self.start_pos, event.position().toPoint()).normalized()
        if rect.width() < 5 or rect.height() < 5:
            self.reject()
            return
        global_top_left = self.mapToGlobal(rect.topLeft())
        self.region = {"x": global_top_left.x(), "y": global_top_left.y(),
                       "w": rect.width(), "h": rect.height()}
        self.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.reject()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(5, 10, 18, 130))
        if self.start_pos and self.end_pos:
            rect = QRect(self.start_pos, self.end_pos).normalized()
            painter.fillRect(rect, QColor(255, 139, 43, 38))
            painter.setPen(QPen(QColor("#FF8B2B"), 3))
            painter.drawRect(rect)
