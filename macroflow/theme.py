"""Shared theme across dashboard, scenario editor and settings."""
BG = "#111419"
SURFACE = "#20252D"
SURFACE_2 = "#292F39"
ACCENT = "#FF8B2B"
FOREGROUND = "#F4F6F8"
MUTED = "#AAB3BE"

STYLE = f"""
QWidget {{ background: {BG}; color: {FOREGROUND}; font: 10pt 'Segoe UI'; }}
QMainWindow, QStackedWidget {{ background: {BG}; }}
QLabel#brand {{ font-size: 23px; font-weight: 800; color: {FOREGROUND}; }}
QLabel#heading {{ font-size: 20px; font-weight: 700; color: {FOREGROUND}; }}
QLabel#muted {{ color: {MUTED}; }}
QFrame#sidebar {{ background: #191E25; border-right: 1px solid #363D48; }}
QFrame#panel, QFrame#card {{ background: {SURFACE}; border: 1px solid #353C47; border-radius: 14px; }}
QFrame#panel QLabel, QFrame#card QLabel {{ background: transparent; }}
QPushButton {{ background: {SURFACE_2}; color: {FOREGROUND}; border: 1px solid #414957;
               border-radius: 9px; padding: 9px 12px; text-align: center; }}
QPushButton:hover {{ background: #353E4A; border-color: {ACCENT}; }}
QPushButton:pressed {{ background: #414954; }}
QPushButton:disabled {{ color: #7A8592; border-color: #333940; }}
QPushButton#primary {{ background: {ACCENT}; color: #111419; border: 1px solid {ACCENT}; font-weight: 700; }}
QPushButton#primary:hover {{ background: #FFAA5F; }}
QPushButton#navigation {{ text-align: left; border: 0; border-radius: 9px; padding: 13px 14px; background: transparent; }}
QPushButton#navigation:checked {{ background: #423224; border-left: 3px solid {ACCENT}; color: {ACCENT}; }}
QLineEdit, QSpinBox, QComboBox {{ background: #151A21; border: 1px solid #4A5361; border-radius: 8px;
                                 min-height: 33px; padding: 3px 9px; selection-background-color: {ACCENT}; }}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{ border: 1px solid {ACCENT}; }}
QComboBox QAbstractItemView {{ background: {SURFACE}; selection-background-color: #523722; }}
QListWidget {{ background: {SURFACE}; border: 1px solid #383F4A; border-radius: 12px; outline: 0; padding: 6px; }}
QListWidget::item {{ border-radius: 8px; padding: 11px; margin: 2px; }}
QListWidget::item:hover {{ background: #303844; }}
QListWidget::item:selected {{ background: #563A26; color: #FFF5E9; border-left: 3px solid {ACCENT}; }}
QCheckBox {{ spacing: 9px; }}
QCheckBox::indicator {{ width: 17px; height: 17px; border-radius: 4px; border: 1px solid #85909D; }}
QCheckBox::indicator:checked {{ background: {ACCENT}; border: 1px solid {ACCENT}; }}
QStatusBar {{ background: #191E25; border-top: 1px solid #303844; color: {MUTED}; }}
QScrollBar:vertical {{ background: transparent; width: 9px; }}
QScrollBar::handle:vertical {{ background: #4A535F; border-radius: 4px; min-height: 30px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
"""
