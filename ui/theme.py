"""Shared visual system for the ScriptNexus desktop interface."""

APP_STYLESHEET = """
QWidget { color: #202333; font-family: "Microsoft YaHei UI", "Segoe UI"; font-size: 13px; }
QMainWindow, QDialog { background: #F5F6FA; }
QToolTip { color: #202333; background: #FFFFFF; border: 1px solid #DADDEA; padding: 6px 8px; }
QPushButton { min-height: 34px; padding: 0 14px; border: 1px solid #DADDEA; border-radius: 8px; background: #FFFFFF; color: #35394C; font-weight: 500; }
QPushButton:hover { background: #F4F4FA; border-color: #C9CCDA; }
QPushButton:pressed { background: #ECECF4; }
QPushButton:disabled { color: #A7AABB; background: #F3F4F8; border-color: #E5E7EF; }
QPushButton[variant="primary"] { color: white; background: #5B5BD6; border-color: #5B5BD6; }
QPushButton[variant="primary"]:hover { background: #4B4BC4; border-color: #4B4BC4; }
QPushButton[variant="danger"] { color: #C83B3B; background: #FFF5F5; border-color: #F2CCCC; }
QPushButton[variant="success"] { color: white; background: #25845B; border-color: #25845B; }
QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox { background: #FFFFFF; border: 1px solid #DADDEA; border-radius: 7px; padding: 7px 9px; selection-background-color: #DCDCFF; selection-color: #202333; }
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus, QSpinBox:focus { border: 2px solid #7272E6; padding: 6px 8px; }
QListWidget, QTreeWidget, QTableWidget { background: #FFFFFF; alternate-background-color: #F8F9FC; border: 1px solid #E3E6EF; border-radius: 8px; outline: none; }
QListWidget::item, QTreeWidget::item { min-height: 30px; padding: 4px 8px; border-radius: 5px; }
QListWidget::item:hover, QTreeWidget::item:hover { background: #F2F2FC; }
QListWidget::item:selected, QTreeWidget::item:selected { color: #4141B7; background: #EAEAFC; }
QHeaderView::section { background: #F7F8FB; color: #62677B; border: none; border-bottom: 1px solid #E3E6EF; padding: 8px; }
QSplitter::handle { background: #E7E9F0; }
QSplitter::handle:hover { background: #CFCFEF; }
QTabWidget::pane { border: 1px solid #E3E6EF; background: #FFFFFF; border-radius: 8px; }
QTabBar::tab { background: transparent; color: #73778A; padding: 8px 14px; margin-right: 2px; }
QTabBar::tab:selected { color: #4B4BC4; font-weight: 600; border-bottom: 2px solid #5B5BD6; }
QGroupBox { font-weight: 600; border: 1px solid #E3E6EF; border-radius: 9px; margin-top: 12px; padding: 14px 12px 10px; background: #FFFFFF; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }
QScrollBar:vertical { width: 10px; background: transparent; margin: 2px; }
QScrollBar::handle:vertical { min-height: 28px; border-radius: 4px; background: #C9CCDA; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QMenu { background: #FFFFFF; border: 1px solid #E3E6EF; padding: 6px; }
QMenu::item { padding: 7px 24px 7px 10px; border-radius: 5px; }
QMenu::item:selected { background: #EEEEFF; color: #4545B8; }
"""


def set_button_variant(button, variant):
    button.setProperty("variant", variant)
    button.style().unpolish(button)
    button.style().polish(button)
