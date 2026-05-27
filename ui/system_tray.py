"""SystemTray - System tray with quick-entry context menu."""

import os
import sys
import platform
import subprocess

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication, QStyle
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QObject, pyqtSignal


class SystemTray(QObject):
    """System tray icon with quick-entry menu.

    Menu Structure:
        打开主窗口
        快速入口 (子菜单)
          ├─ Python 脚本目录
          ├─ WPS Word 模板目录
          ├─ WPS Excel 模板目录
          ├─ Chrome 书签文件目录
        ─────────────────
        退出

    Signals:
        show_main_window: Emitted when user wants to show main window
        quit_triggered: Emitted when user requests quit
    """

    show_main_window = pyqtSignal()
    quit_triggered = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._paths = {
            'python_scripts': '',
            'wps_word': '',
            'wps_excel': '',
            'chrome_bookmarks': '',
        }
        self.tray_icon = QSystemTrayIcon()
        self._setup_icon()
        self._setup_menu()

    def set_paths(self, python_scripts='', wps_word='', wps_excel='', chrome_bookmarks=''):
        """Update quick-entry paths from config."""
        self._paths['python_scripts'] = python_scripts or ''
        self._paths['wps_word'] = wps_word or ''
        self._paths['wps_excel'] = wps_excel or ''
        self._paths['chrome_bookmarks'] = chrome_bookmarks or ''

    def _get_icon_path(self):
        """Get icon path based on platform and bundle mode."""
        if hasattr(sys, '_MEIPASS'):
            base = sys._MEIPASS
        else:
            base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        if platform.system() == 'Windows':
            return os.path.join(base, 'pics', 'icon.ico')
        else:
            return os.path.join(base, 'pics', 'icon.png')

    def _setup_icon(self):
        """Set up tray icon with custom icon."""
        icon_path = self._get_icon_path()

        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        else:
            app = QApplication.instance()
            if app:
                standard_icon = QStyle.StandardPixmap.SP_DesktopIcon
                icon = app.style().standardIcon(standard_icon)
                self.tray_icon.setIcon(icon)
            else:
                self.tray_icon.setIcon(QIcon())

        self.tray_icon.setVisible(True)
        self.tray_icon.setToolTip("脚本管理器")

    def _setup_menu(self):
        """Set up context menu."""
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                padding: 4px;
                font-size: 13px;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 3px;
            }
            QMenu::item:selected {
                background-color: #e8f4fc;
                color: #004C98;
            }
            QMenu::separator {
                height: 1px;
                background: #e0e0e0;
                margin: 4px 8px;
            }
        """)

        # Open Main Window
        self.open_action = QAction("打开主窗口", self)
        self.open_action.triggered.connect(lambda: self.show_main_window.emit())
        menu.addAction(self.open_action)

        # Quick-entry submenu
        self._create_quick_entry_submenu(menu)

        # Separator
        menu.addSeparator()

        # Quit
        self.quit_action = QAction("退出", self)
        self.quit_action.triggered.connect(self._on_quit_requested)
        menu.addAction(self.quit_action)

        self.tray_icon.activated.connect(self._on_activated)
        self.tray_icon.setContextMenu(menu)

    def _create_quick_entry_submenu(self, parent_menu):
        """Create quick-entry submenu for opening module directories."""
        entry_menu = QMenu("快速入口", parent_menu)

        entries = [
            ("Python 脚本目录", 'python_scripts'),
            ("WPS Word 模板目录", 'wps_word'),
            ("WPS Excel 模板目录", 'wps_excel'),
            ("Chrome 书签文件目录", 'chrome_bookmarks'),
        ]

        for label, key in entries:
            action = QAction(label, self)
            action.setData(key)
            action.triggered.connect(
                lambda checked, k=key: self._open_path(k)
            )
            entry_menu.addAction(action)

        parent_menu.addMenu(entry_menu)

    def _open_path(self, key: str):
        """Open a path in the file explorer."""
        path = self._paths.get(key, '')
        if not path:
            return

        # For Chrome bookmarks, the path is a file — open its parent folder
        if key == 'chrome_bookmarks':
            if os.path.isfile(path):
                path = os.path.dirname(path)

        if not os.path.exists(path):
            return

        try:
            if platform.system() == 'Windows':
                os.startfile(path)
            elif platform.system() == 'Darwin':
                subprocess.Popen(['open', path])
            else:
                subprocess.Popen(['xdg-open', path])
        except Exception as e:
            self.show_message("打开失败", f"无法打开路径: {e}", "Warning")

    def _on_activated(self, reason):
        """Handle tray icon activation events."""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_main_window.emit()

    def _on_quit_requested(self):
        """Handle quit request from tray menu."""
        app = QApplication.instance()
        for window in app.topLevelWidgets():
            if hasattr(window, '_force_close'):
                window._force_close = True
                window.close()
        app.quit()

    def show_message(self, title, message, icon="Information", msecs=10000):
        """Display a notification message from the system tray."""
        icon_map = {
            "Information": QSystemTrayIcon.MessageIcon.Information,
            "Warning": QSystemTrayIcon.MessageIcon.Warning,
            "Critical": QSystemTrayIcon.MessageIcon.Critical,
            "None": QSystemTrayIcon.MessageIcon.NoIcon,
        }
        q_icon = icon_map.get(icon, QSystemTrayIcon.MessageIcon.Information)
        self.tray_icon.showMessage(title, message, q_icon, msecs)
