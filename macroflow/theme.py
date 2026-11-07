"""MacroFlow 2.1 graphical theme: graphite surfaces and orange identity."""
from pathlib import Path
import sys

BG = '#101318'
SIDEBAR = '#11161D'
SURFACE = '#191F27'
SURFACE_2 = '#252E39'
ACCENT = '#FF8B2B'
FOREGROUND = '#E9EEF5'
MUTED = '#8793A3'
FONT_PREFERENCES = ('Segoe UI Variable', 'Segoe UI', 'Inter', 'Manrope')


def asset_path(name):
    root = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent.parent))
    return root / 'assets' / name


def stylesheet(font_name='Segoe UI'):
    up = asset_path('chevron_up.png').as_posix()
    down = asset_path('chevron_down.png').as_posix()
    return f"""
* {{ font-family: '{font_name}'; font-size: 13px; color: {FOREGROUND}; }}
QWidget, QMainWindow, QStackedWidget {{ background-color: {BG}; }}
QLabel {{ background: transparent; }}
QLabel#brand {{ font-size: 24px; font-weight: 800; color: #FFFFFF; }}
QLabel#heading {{ font-size: 25px; font-weight: 750; color: {FOREGROUND}; }}
QLabel#sectionTitle {{ font-size: 12px; font-weight: 800; color: {ACCENT}; }}
QLabel#muted {{ font-size: 12px; color: #A5AFBD; }}
QLabel#scenarioTitle {{ font-size: 17px; font-weight: 750; color: #F1F4F8; }}
QLabel#scenarioSubtitle {{ font-size: 12px; color: {MUTED}; }}
QFrame#sidebar {{ background: {SIDEBAR}; border-right: 1px solid #28313D; }}
QFrame#sidebarBrand {{ background: #1A222C; border: 1px solid #303D49; border-radius: 14px; }}
QFrame#panel, QFrame#card {{ background: {SURFACE}; border: 1px solid #303B49; border-radius: 14px; }}
QFrame#panel QLabel, QFrame#card QLabel, QFrame#sidebarBrand QLabel,
QWidget#scenarioContents, QWidget#scenarioContents QLabel {{ background: transparent; }}
QPushButton {{ background: {SURFACE_2}; border: 1px solid #3B4858; border-radius: 10px;
               padding: 8px 13px; min-height: 29px; font-weight: 600; }}
QPushButton:hover {{ background: #303B49; border-color: #637184; }}
QPushButton:pressed {{ background: #3A4553; }}
QPushButton:disabled {{ background: #1F2630; color: #667282; border-color: #303844; }}
QPushButton#primary {{ background: {ACCENT}; border-color: {ACCENT}; color: #12151B; font-weight: 800; }}
QPushButton#primary:hover {{ background: #FFAC63; border-color: #FFAC63; }}
QPushButton#danger:hover {{ background: #39252A; border-color: #D65965; color: #FF929A; }}
QPushButton#navigation {{ text-align: left; background: transparent; border: 1px solid transparent;
                        border-left: 3px solid transparent; border-radius: 9px;
                        min-height: 37px; padding: 10px 12px; font-size: 13px; font-weight: 600; }}
QPushButton#navigation:hover {{ background: #202A35; border-color: #2B3744; }}
QPushButton#navigation:checked {{ background: #372A22; border: 1px solid #5D4330;
                                border-left: 3px solid {ACCENT}; color: #FFB36C; }}
QLineEdit, QSpinBox, QComboBox {{ background: #131920; border: 1px solid #465365; border-radius: 9px;
                                  min-height: 34px; padding: 5px 11px; selection-background-color: {ACCENT}; }}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{ border-color: {ACCENT}; }}
QLineEdit:disabled, QSpinBox:disabled, QComboBox:disabled {{ color: #657386; background: #191F27; }}
QSpinBox {{ padding-right: 37px; }}
QSpinBox::up-button {{ subcontrol-origin: border; subcontrol-position: top right; width: 21px; height: 20px;
                       background: #26303B; border: 0; border-left: 1px solid #485365;
                       border-top-right-radius: 8px; }}
QSpinBox::down-button {{ subcontrol-origin: border; subcontrol-position: bottom right; width: 21px; height: 20px;
                         background: #26303B; border: 0; border-left: 1px solid #485365;
                         border-bottom-right-radius: 8px; }}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {{ background: #58402B; }}
QSpinBox::up-arrow {{ image: url('{up}'); width: 12px; height: 12px; }}
QSpinBox::down-arrow {{ image: url('{down}'); width: 12px; height: 12px; }}
QComboBox {{ padding-right: 36px; }}
QComboBox::drop-down {{ subcontrol-origin: border; subcontrol-position: top right; width: 31px;
                        background: #26303B; border: 0; border-left: 1px solid #485365;
                        border-top-right-radius: 8px; border-bottom-right-radius: 8px; }}
QComboBox::drop-down:hover {{ background: #58402B; }}
QComboBox::down-arrow {{ image: url('{down}'); width: 13px; height: 13px; }}
QComboBox QAbstractItemView {{ background: #222B36; border: 1px solid #48566A; padding: 6px;
                               selection-background-color: #68432C; selection-color: #FFFFFF; outline: none; }}
QListWidget {{ background: #161C24; border: 1px solid #303C49; border-radius: 11px;
               outline: 0; padding: 7px; }}
QListWidget::item {{ background: #202833; border: 1px solid #303B49; border-radius: 9px;
                     padding: 11px 10px; margin: 3px 2px; min-height: 31px; }}
QListWidget::item:hover {{ background: #2B3542; border-color: #516174; }}
QListWidget::item:selected {{ background: #443024; border: 1px solid {ACCENT}; color: #FFF2E4; }}
QListWidget#scenarioList::item {{ padding: 3px; margin: 4px; }}
QCheckBox {{ spacing: 9px; font-weight: 600; }}
QCheckBox::indicator {{ width: 18px; height: 18px; background: #131920; border: 2px solid #6E7D8E; border-radius: 6px; }}
QCheckBox::indicator:hover {{ border-color: {ACCENT}; }}
QCheckBox::indicator:checked {{ background: {ACCENT}; border-color: {ACCENT}; }}
QMenu {{ background: #222A35; border: 1px solid #465367; border-radius: 9px; padding: 6px; }}
QMenu::item {{ padding: 9px 22px; border-radius: 6px; min-width: 155px; }}
QMenu::item:selected {{ background: #60412B; color: #FFD9B7; }}
QMenu::item:disabled {{ color: #758293; }}
QMenu::separator {{ height: 1px; background: #3B4755; margin: 6px; }}
QStatusBar {{ background: #12171E; border-top: 1px solid #2E3946; color: #A3AFBC; }}
QScrollBar:vertical {{ background: #161E27; width: 9px; }}
QScrollBar::handle:vertical {{ background: #4E5B6B; border-radius: 4px; min-height: 24px; }}
QScrollBar::handle:vertical:hover {{ background: #B27846; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{ background: #161E27; height: 9px; }}
QScrollBar::handle:horizontal {{ background: #4E5B6B; border-radius: 4px; min-width: 24px; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
QSplitter::handle {{ background: #11161D; width: 12px; }}
QSplitter::handle:hover {{ background: #654228; }}
QToolTip {{ background: #25303D; border: 1px solid {ACCENT}; padding: 7px; }}
QDialog {{ background: {BG}; }}
QDialogButtonBox QPushButton {{ min-width: 95px; }}
"""

STYLE = stylesheet()
