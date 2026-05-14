"""NavBar - Left navigation bar for the main window."""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PyQt6.QtCore import pyqtSignal, QObject


class NavBar(QWidget):
    """Left navigation bar with fixed width and navigation buttons.

    Navigation items:
        - 首页 (Dashboard)
        - Python 脚本 (Python Scripts)
        - WPS 脚本 (WPS Scripts)
        - JS 脚本 (JS Scripts)
        - 设置 (Settings)

    Signals:
        navigation_requested: Emitted when a navigation button is clicked,
                              passes the target page name as argument
    """

    navigation_requested = pyqtSignal(str)

    # Navigation item constants
    DASHBOARD = "dashboard"
    PYTHON_SCRIPTS = "python_scripts"
    WPS_SCRIPTS = "wps_scripts"
    JS_SCRIPTS = "js_scripts"

    def __init__(self, parent=None):
        """Initialize the navigation bar.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setFixedWidth(180)
        self._setup_ui()

    def _setup_ui(self):
        """Set up the navigation bar UI."""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 20, 10, 20)

        # Create navigation buttons
        self.buttons = {}

        self.buttons[self.DASHBOARD] = self._create_button("首页")
        self.buttons[self.PYTHON_SCRIPTS] = self._create_button("Python 脚本")
        self.buttons[self.WPS_SCRIPTS] = self._create_button("WPS 脚本")
        self.buttons[self.JS_SCRIPTS] = self._create_button("JS 脚本")

        # Add buttons to layout
        for btn_name, btn in self.buttons.items():
            layout.addWidget(btn)

        # Add stretch to push buttons to top
        layout.addStretch()

        self.setLayout(layout)

    def _create_button(self, text):
        """Create a navigation button.

        Args:
            text: Button text

        Returns:
            QPushButton instance
        """
        btn = QPushButton(text)
        btn.setFixedHeight(45)
        btn.clicked.connect(lambda: self._on_button_clicked(text))
        return btn

    def _on_button_clicked(self, text):
        """Handle button click event.

        Args:
            text: Button text that was clicked
        """
        # Map button text to navigation name
        name_map = {
            "首页": self.DASHBOARD,
            "Python 脚本": self.PYTHON_SCRIPTS,
            "WPS 脚本": self.WPS_SCRIPTS,
            "JS 脚本": self.JS_SCRIPTS
        }
        name = name_map.get(text, text)
        self.navigation_requested.emit(name)

    def navigate_to(self, name):
        """Navigate to the specified page.

        Args:
            name: Target page name (dashboard, python_scripts, wps_scripts, js_scripts)
        """
        # Update button styles to show active state
        for btn_name, btn in self.buttons.items():
            if btn_name == name:
                btn.setStyleSheet("QPushButton { background-color: #0078D4; color: white; }")
            else:
                btn.setStyleSheet("QPushButton { background-color: transparent; }")

        # Don't emit signal here - this method is called programmatically, not by user click
        # The signal is only emitted when user clicks a button (in _on_button_clicked)
