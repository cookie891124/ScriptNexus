"""SystemTray - Enhanced system tray with cc-switch style menu."""

import os
import sys
import platform

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication, QStyle
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QObject, pyqtSignal


class SystemTray(QObject):
    """Enhanced system tray icon with cc-switch style context menu.

    Menu Structure:
        打开主窗口
        部署状态 (子菜单)
          ├─ 🟢 Word: 已部署 / 🔴 未部署
          ├─ 🟢 Excel: 已部署 / 🔴 未部署
          ├─ 🟢 Chrome: 已部署 / 🔴 未部署
        ─────────────────
        一键部署
        ─────────────────
        退出

    Signals:
        show_main_window: Emitted when user wants to show main window
        deploy_triggered: Emitted when user triggers deployment
        quit_triggered: Emitted when user requests quit
        status_changed: Emitted when deployment status changes
    """

    show_main_window = pyqtSignal()
    deploy_triggered = pyqtSignal()
    quit_triggered = pyqtSignal()
    status_changed = pyqtSignal(dict)

    # Emoji status indicators (cc-switch style)
    STATUS_OK = "🟢"        # Deployed successfully
    STATUS_PARTIAL = "🟠"   # Partially deployed
    STATUS_ERROR = "🔴"     # Not deployed / Error
    STATUS_UNKNOWN = "⚪"   # Status unknown

    def __init__(self, app=None, deployment_service=None):
        """Initialize the enhanced system tray.

        Args:
            app: QApplication instance (optional)
            deployment_service: DeploymentService for status checking
        """
        super().__init__()
        self.deployment_service = deployment_service
        self._status = {
            'word': self.STATUS_UNKNOWN,
            'excel': self.STATUS_UNKNOWN,
            'chrome': self.STATUS_UNKNOWN,
        }
        self.tray_icon = QSystemTrayIcon()
        self._setup_icon()
        self._setup_menu()
        self._update_tooltip()

    def _get_icon_path(self):
        """Get icon path based on platform and bundle mode."""
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller bundle
            base = sys._MEIPASS
        else:
            # Development mode
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
            # Fallback to standard system icon
            app = QApplication.instance()
            if app:
                standard_icon = QStyle.StandardPixmap.SP_DesktopIcon
                icon = app.style().standardIcon(standard_icon)
                self.tray_icon.setIcon(icon)
            else:
                self.tray_icon.setIcon(QIcon())

        self.tray_icon.setVisible(True)

    def _setup_menu(self):
        """Set up enhanced context menu with cc-switch style."""
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
            QMenu::item:disabled {
                color: #666666;
            }
            QMenu::separator {
                height: 1px;
                background: #e0e0e0;
                margin: 4px 8px;
            }
            QMenu::indicator {
                width: 13px;
                height: 13px;
            }
        """)

        # Action: Open Main Window
        self.open_action = QAction("打开主窗口", self)
        self.open_action.triggered.connect(lambda: self.show_main_window.emit())
        menu.addAction(self.open_action)

        # Status submenu with emoji indicators
        self._create_status_submenu(menu)

        # Separator
        menu.addSeparator()

        # Action: Quick Deploy
        self.deploy_action = QAction("一键部署", self)
        self.deploy_action.triggered.connect(lambda: self.deploy_triggered.emit())
        menu.addAction(self.deploy_action)

        # Separator
        menu.addSeparator()

        # Action: Quit
        self.quit_action = QAction("退出", self)
        self.quit_action.triggered.connect(self._on_quit_requested)
        menu.addAction(self.quit_action)

        # Connect activated signal for double-click handling
        self.tray_icon.activated.connect(self._on_activated)

        # Set the context menu
        self.tray_icon.setContextMenu(menu)

    def _create_status_submenu(self, parent_menu):
        """Create deployment status submenu with emoji indicators."""
        status_menu = QMenu("部署状态", parent_menu)

        # Word status (display only, grayed out)
        self.word_status_action = QAction(f"{self.STATUS_UNKNOWN} Word", self)
        self.word_status_action.setEnabled(False)
        status_menu.addAction(self.word_status_action)

        # Excel status
        self.excel_status_action = QAction(f"{self.STATUS_UNKNOWN} Excel", self)
        self.excel_status_action.setEnabled(False)
        status_menu.addAction(self.excel_status_action)

        # Chrome status
        self.chrome_status_action = QAction(f"{self.STATUS_UNKNOWN} Chrome", self)
        self.chrome_status_action.setEnabled(False)
        status_menu.addAction(self.chrome_status_action)

        parent_menu.addMenu(status_menu)
        self.status_menu = status_menu

    def update_status(self, status_dict):
        """Update deployment status indicators.

        Args:
            status_dict: Dictionary with 'word', 'excel', 'chrome' keys
                        Values: 'ok', 'partial', 'error', 'unknown'
        """
        status_map = {
            'ok': self.STATUS_OK,
            'partial': self.STATUS_PARTIAL,
            'error': self.STATUS_ERROR,
            'unknown': self.STATUS_UNKNOWN,
        }

        self._status['word'] = status_map.get(status_dict.get('word', 'unknown'), self.STATUS_UNKNOWN)
        self._status['excel'] = status_map.get(status_dict.get('excel', 'unknown'), self.STATUS_UNKNOWN)
        self._status['chrome'] = status_map.get(status_dict.get('chrome', 'unknown'), self.STATUS_UNKNOWN)

        # Update action text
        self.word_status_action.setText(f"{self._status['word']} Word")
        self.excel_status_action.setText(f"{self._status['excel']} Excel")
        self.chrome_status_action.setText(f"{self._status['chrome']} Chrome")

        # Update tooltip
        self._update_tooltip()

        # Emit status changed signal
        self.status_changed.emit(self._status)

    def _update_tooltip(self):
        """Build and set tooltip text from current status."""
        lines = ["脚本管理器", "部署状态:"]
        lines.append(f"  Word: {self._status['word']}")
        lines.append(f"  Excel: {self._status['excel']}")
        lines.append(f"  Chrome: {self._status['chrome']}")
        tooltip = "\n".join(lines)
        self.tray_icon.setToolTip(tooltip)

    def _on_activated(self, reason):
        """Handle tray icon activation events."""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_main_window.emit()

    def _on_quit_requested(self):
        """Handle quit request from tray menu."""
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        for window in app.topLevelWidgets():
            if hasattr(window, '_force_close'):
                window._force_close = True
                window.close()
        app.quit()

    def show_message(self, title, message, icon="Information", msecs=10000):
        """Display a notification message from the system tray.

        Args:
            title: The title of the notification
            message: The message content
            icon: Message icon type - "Information", "Warning", "Critical", or "None"
            msecs: Display duration in milliseconds
        """
        icon_map = {
            "Information": QSystemTrayIcon.MessageIcon.Information,
            "Warning": QSystemTrayIcon.MessageIcon.Warning,
            "Critical": QSystemTrayIcon.MessageIcon.Critical,
            "None": QSystemTrayIcon.MessageIcon.NoIcon,
        }
        q_icon = icon_map.get(icon, QSystemTrayIcon.MessageIcon.Information)
        self.tray_icon.showMessage(title, message, q_icon, msecs)

    def refresh_status(self):
        """Refresh deployment status from deployment service."""
        if self.deployment_service:
            status = self.deployment_service.check_deployment_status()
            self.update_status(status)