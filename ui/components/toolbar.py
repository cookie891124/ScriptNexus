"""Top command bar for ScriptNexus."""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel

from ui.theme import set_button_variant


class ToolBar(QWidget):
    import_requested = pyqtSignal()
    export_requested = pyqtSignal()
    settings_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(70)
        self.setObjectName("topBar")
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet("""
            QWidget#topBar { background: #FFFFFF; border-bottom: 1px solid #E6E8F0; }
            QLabel#appTitle { color: #242738; font-size: 17px; font-weight: 700; }
            QLabel#appSubtitle { color: #8B8FA2; font-size: 11px; }
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 10, 24, 10)
        layout.setSpacing(10)

        titles = QVBoxLayout()
        titles.setSpacing(0)
        self.title_label = QLabel("自动化工作台")
        self.title_label.setObjectName("appTitle")
        subtitle = QLabel("集中管理、运行与部署办公脚本")
        subtitle.setObjectName("appSubtitle")
        titles.addWidget(self.title_label)
        titles.addWidget(subtitle)
        layout.addLayout(titles)
        layout.addStretch()

        self.import_button = self._create_button("导入")
        self.import_button.clicked.connect(self.import_requested.emit)
        layout.addWidget(self.import_button)
        self.export_button = self._create_button("导出")
        set_button_variant(self.export_button, "primary")
        self.export_button.clicked.connect(self.export_requested.emit)
        layout.addWidget(self.export_button)
        self.settings_button = self._create_button("设置")
        self.settings_button.clicked.connect(self.settings_requested.emit)
        layout.addWidget(self.settings_button)

    @staticmethod
    def _create_button(text):
        button = QPushButton(text)
        button.setFixedHeight(38)
        button.setMinimumWidth(76)
        return button
