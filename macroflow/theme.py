"""One reusable, accent-forward design system for every MacroFlow view."""
from pathlib import Path
import sys

BG = "#111419"
SIDEBAR = "#191F27"
SURFACE = "#202630"
SURFACE_2 = "#303844"
ACCENT = "#FF8B2B"
FOREGROUND = "#F4F6F8"
MUTED = "#AFB9C6"
FONT_PREFERENCES = ("Segoe UI Variable", "Segoe UI", "Inter", "Manrope")


def asset_path(name):
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return root / "assets" / name


def stylesheet(font_name="Segoe UI"):
    up = asset_path("chevron_up.png").as_posix()
    down = asset_path("chevron_down.png").as_posix()
    # QSS subcontrols are styled explicitly: no native blue/gray arrows remain.
    return f"""
QWidget {{ background: {BG}; color: {FOREGROUND}; font-family: '{font_name}'; font-size: 13px; }}
QMainWindow, QStackedWidget {{ background: {BG}; }}
QLabel#brand {{ font-size: 23px; font-weight: 800; color: {FOREGROUND}; }}
QLabel#heading {{ font-size: 23px; font-weight: 750; color: {FOREGROUND}; }}
QLabel#sectionTitle {{ font-size: 13px; font-weight: 800; color: {ACCENT}; }}
QLabel#muted {{ font-size: 13px; color: {MUTED}; }}
QLabel#scenarioTitle {{ font-size: 17px; font-weight: 800; color: {FOREGROUND}; background: transparent; }}
QLabel#scenarioSubtitle {{ font-size: 13px; color: {MUTED}; background: transparent; }}
QFrame#sidebar {{ background: {SIDEBAR}; border-right: 1px solid #37404D; }}
QFrame#sidebarBrand {{ background: #222A34; border: 1px solid #414957; border-radius: 13px; }}
QFrame#panel, QFrame#card {{ background: {SURFACE}; border: 1px solid #394350; border-radius: 14px; }}
QFrame#panel QLabel, QFrame#card QLabel, QFrame#sidebarBrand QLabel {{ background: transparent; }}
QWidget#scenarioContents, QWidget#scenarioContents QLabel {{ background: transparent; }}
QPushButton {{ background: {SURFACE_2}; color: {FOREGROUND}; border: 1px solid #485462;
               border-radius: 9px; min-height: 23px; padding: 9px 12px; font-weight: 600; }}
QPushButton:hover {{ background: #3B4654; border-color: {ACCENT}; }}
QPushButton:pressed {{ background: #4B5460; }}
QPushButton:disabled {{ color: #77828F; border-color: #323B45; background: #252B33; }}
QPushButton#primary {{ background: {ACCENT}; color: #12171D; border: 1px solid {ACCENT}; font-weight: 800; }}
QPushButton#primary:hover {{ background: #FFAA63; }}
QPushButton#danger:hover {{ border-color: #FF6262; color: #FF8888; }}
QPushButton#navigation {{ text-align: left; border: 1px solid #3A4451; border-left: 4px solid #3A4451;
                         border-radius: 10px; min-height: 35px; padding: 10px 15px; background: #242C37; font-size: 14px; font-weight: 650; }}
QPushButton#navigation:hover {{ border-color: {ACCENT}; background: #34323A; }}
QPushButton#navigation:checked {{ background: #423225; border: 1px solid #7A532C; border-left: 4px solid {ACCENT}; color: #FFB56D; }}
QLineEdit, QSpinBox, QComboBox {{ background: #151B23; color: {FOREGROUND}; border: 1px solid #525F6E;
                                 border-radius: 9px; min-height: 35px; padding: 4px 10px; selection-background-color: {ACCENT}; }}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{ border-color: {ACCENT}; }}
QSpinBox {{ padding-right: 45px; }}
QSpinBox::up-button {{ subcontrol-origin: border; subcontrol-position: top right; width: 23px; height: 20px;
                       background: #2C3540; border: 0px; border-left: 1px solid #505B68;
                       border-top-right-radius: 8px; }}
QSpinBox::down-button {{ subcontrol-origin: border; subcontrol-position: bottom right; width: 23px; height: 20px;
                         background: #2C3540; border: 0px; border-left: 1px solid #505B68;
                         border-bottom-right-radius: 8px; }}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {{ background: #4A3829; }}
QSpinBox::up-arrow {{ image: url('{up}'); width: 12px; height: 12px; }}
QSpinBox::down-arrow {{ image: url('{down}'); width: 12px; height: 12px; }}
QComboBox {{ padding-right: 36px; }}
QComboBox::drop-down {{ subcontrol-origin: border; subcontrol-position: top right; width: 34px;
                        background: #2C3540; border: 0px; border-left: 1px solid #505B68;
                        border-top-right-radius: 8px; border-bottom-right-radius: 8px; }}
QComboBox::drop-down:hover {{ background: #4A3829; }}
QComboBox::down-arrow {{ image: url('{down}'); width: 13px; height: 13px; }}
QComboBox QAbstractItemView {{ background: {SURFACE}; color: {FOREGROUND}; border: 1px solid #5A6572;
                               selection-background-color: #684228; selection-color: #FFFFFF; padding: 5px; outline: none; }}
QListWidget {{ background: {SURFACE}; color: {FOREGROUND}; border: 1px solid #3B4451; border-radius: 12px;
               outline: none; padding: 6px; }}
QListWidget::item {{ border: 1px solid transparent; border-radius: 9px; padding: 10px; margin: 3px; }}
QListWidget::item:hover {{ background: #303A46; }}
QListWidget::item:selected {{ background: #4B382A; color: #FFF8F0; border-left: 4px solid {ACCENT}; border-top: 1px solid #72502F; border-bottom: 1px solid #72502F; }}
QListWidget#scenarioList::item {{ padding: 3px; margin: 4px; }}
QCheckBox {{ spacing: 9px; font-weight: 550; }}
QCheckBox::indicator {{ width: 19px; height: 19px; border-radius: 6px; border: 2px solid #8C9BAA; background: #151B23; }}
QCheckBox::indicator:hover {{ border-color: {ACCENT}; }}
QCheckBox::indicator:checked {{ background: {ACCENT}; border: 2px solid {ACCENT}; }}
QMenu {{ background: #242C36; color: {FOREGROUND}; border: 1px solid #505C6A; border-radius: 10px; padding: 7px; }}
QMenu::item {{ background: transparent; padding: 9px 27px 9px 18px; border-radius: 6px; min-width: 155px; }}
QMenu::item:selected {{ background: #59402D; color: #FFD0A5; }}
QMenu::item:disabled {{ color: #83909C; }}
QMenu::separator {{ height: 1px; background: #45505C; margin: 6px 8px; }}
QStatusBar {{ background: {SIDEBAR}; border-top: 1px solid #39434D; color: {MUTED}; }}
QScrollBar:vertical {{ background: #1B212A; width: 11px; }}
QScrollBar::handle:vertical {{ background: #596372; border-radius: 5px; min-height: 35px; }}
QScrollBar::handle:vertical:hover {{ background: #BE7940; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
QScrollBar:horizontal {{ background: #1B212A; height: 11px; }}
QScrollBar::handle:horizontal {{ background: #596372; border-radius: 5px; min-width: 35px; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0px; }}
QSplitter::handle {{ background: #343F4B; width: 6px; }}
QSplitter::handle:hover {{ background: {ACCENT}; }}
QToolTip {{ background: #222B35; color: {FOREGROUND}; border: 1px solid {ACCENT}; padding: 6px; }}
QDialog {{ background: {BG}; }}
QDialogButtonBox QPushButton {{ min-width: 95px; }}
"""

STYLE = stylesheet()
