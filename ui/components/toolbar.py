"""ToolBar - Top toolbar for the main window."""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import pyqtSignal


class ToolBar(QWidget):
    """Top toolbar with fixed height and action buttons.

    Features:
        - Title label "脚本管理器"
        - Action buttons: 一键部署，导入，导出，设置

    Signals:
        deploy_requested: Emitted when deploy button is clicked
        import_requested: Emitted when import button is clicked
        export_requested: Emitted when export button is clicked
        settings_requested: Emitted when settings button is clicked
    """

    deploy_requested = pyqtSignal()
    import_requested = pyqtSignal()
    export_requested = pyqtSignal()
    settings_requested = pyqtSignal()

    def __init__(self, parent=None):
        """Initialize the toolbar.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setFixedHeight(50)
        self._setup_ui()

    def _setup_ui(self):
        """Set up the toolbar UI."""
        layout = QHBoxLayout()
        layout.setContentsMargins(20, 5, 20, 5)
        layout.setSpacing(15)

        # Title label
        self.title_label = QLabel("脚本管理器")
        self.title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #333;
            }
        """)
        layout.addWidget(self.title_label)

        # Add stretch to push buttons to right
        layout.addStretch()

        # Action buttons
        self.deploy_button = self._create_button("一键部署")
        self.deploy_button.clicked.connect(self.deploy_requested.emit)
        layout.addWidget(self.deploy_button)

        self.import_button = self._create_button("导入")
        self.import_button.clicked.connect(self.import_requested.emit)
        layout.addWidget(self.import_button)

        self.export_button = self._create_button("导出")
        self.export_button.clicked.connect(self.export_requested.emit)
        layout.addWidget(self.export_button)

        # Settings button
        self.settings_button = self._create_button("设置")
        self.settings_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:pressed {
                background-color: #4e5861;
            }
        """)
        self.settings_button.clicked.connect(self.settings_requested.emit)
        layout.addWidget(self.settings_button)

        self.setLayout(layout)

    def _create_button(self, text):
        """Create an action button.

        Args:
            text: Button text

        Returns:
            QPushButton instance
        """
        btn = QPushButton(text)
        btn.setFixedHeight(35)
        btn.setMinimumWidth(80)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #0078D4;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #006CBE;
            }
            QPushButton:pressed {
                background-color: #005A9E;
            }
        """)
        return btn
