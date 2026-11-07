"""MacroFlow UI 3.1 — shared visual tokens and unified Qt style for every screen."""
from pathlib import Path
import sys

BG = '#0C1119'
SIDEBAR = '#0B1018'
SURFACE = '#141B26'
SURFACE_2 = '#1A2430'
ACCENT = '#FF8A24'
FOREGROUND = '#EAF0F8'
MUTED = '#AAB6C7'
FONT_PREFERENCES = ('Segoe UI Variable', 'Inter', 'Manrope', 'Segoe UI')


def asset_path(name):
    root = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent.parent))
    return root / 'assets' / name


def stylesheet(font_name='Segoe UI'):
    up = asset_path('chevron_up.png').as_posix()
    down = asset_path('chevron_down.png').as_posix()
    return f"""
* {{ font-family: '{font_name}'; font-size: 13px; color: {FOREGROUND}; }}
QMainWindow, QWidget, QStackedWidget {{ background: {BG}; }}
QLabel {{ background: transparent; }}
QFrame#titleBar {{ background: #0B1017; border-bottom: 1px solid #283140; }}
QLabel#windowTitle {{ font-size: 12px; font-weight: 700; color: #E9EFF8; }}
QLabel#windowVersion {{ color: #9DA8BA; font-size: 12px; padding-left: 6px; }}
QPushButton#titleButton, QPushButton#titleClose {{ background: transparent; border: none; border-radius: 7px;
                                                      min-height: 33px; min-width: 43px; max-width: 43px; padding: 0; }}
QPushButton#titleButton:hover {{ background: #253141; }}
QPushButton#titleClose:hover {{ background: #A9323E; }}
QPushButton#titleButton:pressed, QPushButton#titleClose:pressed {{ background: #694031; }}
QFrame#sidebar {{ background: #0E131B; border-right: 1px solid #303947; }}
QFrame#brandArea {{ background: transparent; border: none; }}
QLabel#brandTitle {{ color: #FFFFFF; font-size: 20px; font-weight: 900; }}
QLabel#brandSubtitle {{ color: #B2BECF; font-size: 10px; letter-spacing: 1px; }}
QLabel#navSection {{ color: #8F9BAB; font-size: 11px; font-weight: 700; }}
QFrame#sidebarDivider {{ background: #273140; min-height: 1px; max-height: 1px; border: none; }}
QFrame#sidebarFooter {{ background: transparent; }}
QLabel#sidebarStatus {{ color: #D9E2EE; font-size: 12px; }}
QLabel#shortcutHint {{ color: #B1BCCD; font-size: 11px; }}
QLabel#keycap {{ background: #252D39; border-radius: 5px; color: #F0F4FA;
                 font-size: 11px; font-weight: 800; padding: 3px 5px; }}
QPushButton {{ background: #222C3A; border: 1px solid #3C4858; border-radius: 9px;
               color: #E8EFF8; min-height: 35px; padding: 5px 13px; font-weight: 650; }}
QPushButton:hover {{ background: #303C4D; border-color: #8B6850; }}
QPushButton:pressed {{ background: #4C382B; border-color: #FF8A24; padding-top: 7px; padding-bottom: 3px; }}
QPushButton:focus {{ border-color: #FF963D; }}
QPushButton:disabled {{ background: #19212C; border-color: #2B3441; color: #748193; }}
QPushButton#primary {{ background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #FFA442,stop:1 #FF820C);
                       color: #141516; font-weight: 850; border: 1px solid #FFAD4B; }}
QPushButton#primary:hover {{ background: #FFB351; border-color: #FFC77E; }}
QPushButton#primary:pressed {{ background: #DB6A09; border-color: #F98A24; }}
QPushButton#iconButton {{ min-width: 36px; max-width: 43px; min-height: 34px;
                         padding: 2px; background: #1B2532; border: 1px solid #344355; }}
QPushButton#iconButton:hover {{ background: #3B332D; border-color: #FF8A24; }}
QPushButton#iconButton:pressed {{ background: #674027; }}
QPushButton#iconButton:checked {{ background: #623B24; border-color: #FF8A24; }}
QPushButton#navigation {{ text-align: left; min-height: 43px; padding: 6px 13px;
                          background: transparent; border: 1px solid transparent;
                          font-weight: 650; font-size: 13px; border-radius: 10px; }}
QPushButton#navigation:hover {{ background: #25303E; border-color: #49576A; }}
QPushButton#navigation:checked {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #754020,stop:1 #4A2B1E);
                                 border: 1px solid #FF8A24; color: #FFFFFF; font-weight: 800; }}
QPushButton#navigation:pressed {{ background: #AA5A22; }}
QPushButton#quickAction {{ background: #19222E; text-align: left; min-height: 32px;
                         border: 1px solid #303C4C; font-size: 12px; }}
QPushButton#quickAction:hover {{ background: #2E3440; border-color: #FF8A24; }}
QPushButton#record {{ background: #242C38; border-color: #4B586A; }}
QPushButton#record:hover {{ background: #493328; border-color: #F98B30; }}
QPushButton#record:checked {{ background: #682D25; border-color: #FF684F; }}
QPushButton#danger {{ background: #2D2933; border-color: #624858; color: #F7CBD1; }}
QPushButton#danger:hover {{ background: #58313A; border-color: #EC737E; }}
QFrame#pageHeader {{ background: transparent; border: none; }}
QLabel#pageTitle {{ color: #FFFFFF; font-size: 24px; font-weight: 850; }}
QLabel#pageSubtitle {{ color: #AAB5C4; font-size: 13px; }}
QLabel#sectionTitle {{ color: #F4F6F9; font-weight: 800; font-size: 15px; }}
QLabel#sectionKicker {{ color: #FFAE59; font-weight: 800; font-size: 11px; }}
QLabel#muted {{ color: #A7B3C3; font-size: 12px; }}
QLabel#mutedSmall {{ color: #8E9BAD; font-size: 11px; }}
QLabel#hint {{ color: #BBC5D3; font-size: 12px; }}
QLabel#accent {{ color: #FFAA51; font-weight: 850; font-size: 12px; }}
QLabel#countPill {{ background: #242C39; border-radius: 6px; color: #D8E2F0;
                    padding: 3px 7px; font-weight: 750; font-size: 12px; }}
QLabel#scenarioTitle {{ color: #F6F8FC; font-weight: 850; font-size: 16px; }}
QLabel#scenarioSubtitle {{ color: #A9B8C8; font-size: 12px; }}
QLabel#scenarioOpen {{ color: #FFAF5F; font-size: 12px; font-weight: 750; }}
QLabel#stepTitle {{ font-weight: 750; color: #F3F6FB; font-size: 13px; }}
QLabel#stepDetails {{ font-size: 11px; color: #A7B4C6; }}
QLabel#stepIndex {{ font-size: 12px; font-weight: 800; color: #D8E0EB; }}
QLabel#stepDelay {{ background: #2A3442; color: #CDD7E4; padding: 6px 9px; border-radius: 7px;
                    font-size: 11px; }}
QLabel#actionHeading {{ font-size: 17px; font-weight: 850; color: #F6F8FB; }}
QLabel#actionDetails {{ font-size: 12px; color: #ADB9C9; }}
QLabel#fieldLabel {{ color: #CFD9E6; font-size: 12px; font-weight: 600; }}
QFrame#panel, QFrame#card, QFrame#parameterPanel, QFrame#transportPanel,
QFrame#inspectorPanel, QFrame#workPanel, QFrame#logPanel {{ background: #151C27;
                    border: 1px solid #303B4B; border-radius: 13px; }}
QFrame#panel QLabel, QFrame#card QLabel, QFrame#parameterPanel QLabel,
QFrame#transportPanel QLabel, QFrame#inspectorPanel QLabel,
QFrame#workPanel QLabel, QFrame#logPanel QLabel,
QWidget#scenarioContents QLabel, QWidget#stepContents QLabel {{ background: transparent; }}
QFrame#inspectorHeading {{ background: #202A38; border: 1px solid #344353; border-radius: 9px; }}
QFrame#inspectorHeading QLabel {{ background: transparent; }}
QFrame#helpCard {{ background: #212C3A; border: 1px solid #445267; border-radius: 10px; }}
QFrame#helpCard QLabel {{ background: transparent; }}
QFrame#separator {{ background: #303A4A; border: none; min-height: 1px; max-height: 1px; }}
QFrame#actionIconBox {{ background: #5B3927; border: 1px solid #84502E; border-radius: 10px; }}
QFrame#stepIconBox {{ background: #253142; border: 1px solid #354153; border-radius: 8px; }}
QWidget#scenarioContents, QWidget#stepContents {{ background: transparent; }}
QLineEdit, QSpinBox, QComboBox {{ background: #101722; border: 1px solid #435063;
  border-radius: 8px; padding: 5px 10px; min-height: 32px; color: #ECF2FA;
  selection-background-color: #9B5428; selection-color: #FFFFFF; }}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{ border: 1px solid #FF922F; }}
QLineEdit:disabled, QSpinBox:disabled, QComboBox:disabled {{ color: #718196; background: #19212C; }}
QSpinBox {{ padding-right: 30px; }}
QSpinBox::up-button {{ subcontrol-origin: border; subcontrol-position: top right; width: 21px; height: 19px;
                       background: #273343; border: none; border-left: 1px solid #4F5B6C; border-top-right-radius: 8px; }}
QSpinBox::down-button {{ subcontrol-origin: border; subcontrol-position: bottom right; width: 21px; height: 19px;
                         background: #273343; border: none; border-left: 1px solid #4F5B6C; border-bottom-right-radius: 8px; }}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {{ background: #72442C; }}
QSpinBox::up-arrow {{ image: url('{up}'); width: 10px; height: 10px; }}
QSpinBox::down-arrow {{ image: url('{down}'); width: 10px; height: 10px; }}
QComboBox {{ padding-right: 34px; }}
QComboBox::drop-down {{ subcontrol-origin: border; subcontrol-position: top right; width: 30px;
                        border: none; border-left: 1px solid #49576A; border-top-right-radius: 8px;
                        border-bottom-right-radius: 8px; background: #273343; }}
QComboBox::drop-down:hover {{ background: #70442C; }}
QComboBox::down-arrow {{ image: url('{down}'); width: 12px; height: 12px; }}
QComboBox QAbstractItemView {{ background: #1C2532; border: 1px solid #526174;
 selection-background-color: #69422C; selection-color: #FFFFFF; padding: 5px; outline: 0; }}
QListWidget {{ background: transparent; border: none; outline: 0; padding: 0; }}
QListWidget::item {{ background: #1A2430; border: 1px solid #303D4D;
                     border-radius: 9px; margin: 3px 1px; padding: 0; }}
QListWidget::item:hover {{ background: #27313E; border-color: #795437; }}
QListWidget::item:selected {{ background: #482D20; border: 1px solid #FF8A24; }}
QListWidget#scenarioList::item {{ margin: 4px 1px; }}
QCheckBox {{ spacing: 9px; font-weight: 650; }}
QCheckBox::indicator {{ width: 17px; height: 17px; background: #101723;
                         border: 2px solid #748397; border-radius: 5px; }}
QCheckBox::indicator:hover {{ border-color: #FF9C45; }}
QCheckBox::indicator:checked {{ background: #FF8A24; border-color: #FF8A24; }}
QMenu {{ background: #1D2734; border: 1px solid #4A596C; border-radius: 9px; padding: 6px; }}
QMenu::item {{ background: transparent; min-width: 170px; padding: 8px 20px;
                border-radius: 5px; font-size: 12px; }}
QMenu::item:selected {{ background: #553826; color: #FFFFFF; }}
QMenu::separator {{ height: 1px; background: #495468; margin: 4px 9px; }}
QSplitter::handle {{ background: #0D141D; width: 10px; }}
QSplitter::handle:hover {{ background: #FF8A24; }}
QScrollBar:vertical {{ background: #131B26; width: 9px; margin: 0; }}
QScrollBar::handle:vertical {{ background: #526073; border-radius: 4px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: #D8863D; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{ background: #131B26; height: 8px; }}
QScrollBar::handle:horizontal {{ background: #526073; border-radius: 4px; min-width: 26px; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
QPlainTextEdit {{ background: #121924; border: none; selection-background-color: #75452B;
                  color: #BBC8D7; font-family: 'Consolas'; font-size: 12px; }}
QToolTip {{ background: #232E3D; border: 1px solid #FF8A24; padding: 7px; color: #FFFFFF; }}
QDialog, QMessageBox {{ background: #141C27; }}
QDialogButtonBox QPushButton {{ min-width: 95px; }}
"""

STYLE = stylesheet()
