"""Left navigation for the ScriptNexus workspace."""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel


class NavBar(QWidget):
    navigation_requested = pyqtSignal(str)

    DASHBOARD = "dashboard"
    PYTHON_SCRIPTS = "python_scripts"
    WPS_SCRIPTS = "wps_scripts"
    JS_SCRIPTS = "js_scripts"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(218)
        self.setObjectName("navBar")
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet("""
            QWidget#navBar { background: #FFFFFF; border-right: 1px solid #E6E8F0; }
            QLabel#brandMark { color: white; background: #5B5BD6; border-radius: 9px; font-size: 16px; font-weight: 700; }
            QLabel#brandName { color: #242738; font-size: 16px; font-weight: 700; }
            QLabel#brandTagline { color: #9296A8; font-size: 10px; }
            QLabel#sectionLabel { color: #9A9DAE; font-size: 10px; font-weight: 600; padding-left: 8px; }
            QPushButton { text-align: left; padding-left: 16px; border: none; border-radius: 8px; background: transparent; color: #686C7F; font-weight: 500; }
            QPushButton:hover { background: #F4F4FA; color: #3D4052; }
            QPushButton:checked { background: #EEEEFF; color: #4B4BC4; font-weight: 600; }
        """)
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(14, 20, 14, 18)

        brand = QHBoxLayout()
        brand.setSpacing(10)
        mark = QLabel("SN")
        mark.setObjectName("brandMark")
        mark.setFixedSize(40, 40)
        mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand.addWidget(mark)
        brand_text = QVBoxLayout()
        brand_text.setSpacing(0)
        name = QLabel("ScriptNexus")
        name.setObjectName("brandName")
        tagline = QLabel("自动化脚本工作台")
        tagline.setObjectName("brandTagline")
        brand_text.addWidget(name)
        brand_text.addWidget(tagline)
        brand.addLayout(brand_text)
        layout.addLayout(brand)
        layout.addSpacing(24)

        section = QLabel("工作空间")
        section.setObjectName("sectionLabel")
        layout.addWidget(section)
        layout.addSpacing(4)

        self.buttons = {
            self.DASHBOARD: self._create_button("总览", self.DASHBOARD),
            self.PYTHON_SCRIPTS: self._create_button("Python 脚本", self.PYTHON_SCRIPTS),
            self.WPS_SCRIPTS: self._create_button("WPS 脚本", self.WPS_SCRIPTS),
            self.JS_SCRIPTS: self._create_button("Chrome JS", self.JS_SCRIPTS),
        }
        for button in self.buttons.values():
            layout.addWidget(button)
        layout.addStretch()

    def _create_button(self, text, name):
        button = QPushButton(text)
        button.setFixedHeight(42)
        button.setCheckable(True)
        button.clicked.connect(lambda checked=False, target=name: self.navigation_requested.emit(target))
        return button

    def navigate_to(self, name):
        for button_name, button in self.buttons.items():
            button.setChecked(button_name == name)
