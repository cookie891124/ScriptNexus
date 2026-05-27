"""SettingsDialog - Settings dialog for configuring paths and preferences."""

import os
import platform
import sys
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QGroupBox,
    QFormLayout,
    QTabWidget,
    QWidget,
    QTextEdit,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class SettingsDialog(QDialog):
    """Settings dialog for application configuration.

    Tabs:
        - Paths - Configure Chrome and WPS paths
        - About - Application information
    """

    def __init__(self, path_detection_service, config_service, parent=None):
        """Initialize the SettingsDialog.

        Args:
            path_detection_service: PathDetectionService instance for auto-detection
            config_service: ConfigService instance for saving/loading configuration
            parent: Parent widget
        """
        super().__init__(parent)
        self.path_detection_service = path_detection_service
        self.config_service = config_service

        self.setWindowTitle("设置")
        self.setMinimumSize(700, 500)
        self.setModal(True)

        self._setup_ui()
        self._load_config()

    def _setup_ui(self):
        """Set up the SettingsDialog UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)

        # Tab widget
        self.tabs = QTabWidget()

        # Paths tab
        self.paths_tab = PathsTab(self.path_detection_service)
        self.tabs.addTab(self.paths_tab, "路径配置")

        # About tab (placeholder)
        self.about_tab = AboutTab()
        self.tabs.addTab(self.about_tab, "关于")

        layout.addWidget(self.tabs)

        # Buttons — Save saves paths, Close dismisses
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Close
        )
        button_box.button(QDialogButtonBox.StandardButton.Save).setText("保存")
        button_box.button(QDialogButtonBox.StandardButton.Close).setText("关闭")

        button_box.accepted.connect(self._on_save)
        button_box.rejected.connect(self.reject)

        layout.addWidget(button_box)
        self.setLayout(layout)

    def _load_config(self):
        """Load configuration from config service."""
        self.paths_tab.scripts_dir_input.setText(
            self.config_service.get("paths.scripts_dir", "")
        )
        self.paths_tab.word_startup_input.setText(
            self.config_service.get("paths.wps_word_startup", "")
        )
        self.paths_tab.excel_startup_input.setText(
            self.config_service.get("paths.wps_excel_startup", "")
        )
        self.paths_tab.chrome_path_input.setText(
            self.config_service.get("paths.chrome_bookmarks", "")
        )

    def _on_save(self):
        """Save configuration."""
        # Save paths
        self.paths_tab.save_config(self.config_service)

        # Accept dialog - MainWindow will handle refresh and message
        self.accept()


class PathsTab(QWidget):
    """Paths configuration tab."""

    def __init__(self, path_detection_service, parent=None):
        """Initialize the PathsTab.

        Args:
            path_detection_service: PathDetectionService instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.path_detection_service = path_detection_service
        self._setup_ui()

    def _setup_ui(self):
        """Set up the PathsTab UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(20)

        # Python configuration group (matches left nav order)
        python_group = QGroupBox("Python 配置")
        python_layout = QFormLayout()
        python_layout.setSpacing(10)

        self.scripts_dir_input = QLineEdit()
        self.scripts_dir_input.setPlaceholderText("Python 脚本存储目录")
        scripts_browse_btn = QPushButton("浏览...")
        scripts_browse_btn.clicked.connect(self._browse_scripts_dir)

        scripts_dir_layout = QHBoxLayout()
        scripts_dir_layout.addWidget(self.scripts_dir_input)
        scripts_dir_layout.addWidget(scripts_browse_btn)
        python_layout.addRow("脚本目录:", scripts_dir_layout)

        python_group.setLayout(python_layout)
        layout.addWidget(python_group)

        # WPS group
        wps_group = QGroupBox("WPS 配置")
        wps_layout = QFormLayout()
        wps_layout.setSpacing(10)

        self.word_startup_input = QLineEdit()
        self.word_startup_input.setPlaceholderText("Word 模板文件输出目录")
        word_browse_btn = QPushButton("浏览...")
        word_browse_btn.clicked.connect(self._browse_word_startup)

        word_startup_layout = QHBoxLayout()
        word_startup_layout.addWidget(self.word_startup_input)
        word_startup_layout.addWidget(word_browse_btn)
        wps_layout.addRow("Word 模板目录:", word_startup_layout)

        self.excel_startup_input = QLineEdit()
        self.excel_startup_input.setPlaceholderText("Excel 模板文件输出目录")
        excel_browse_btn = QPushButton("浏览...")
        excel_browse_btn.clicked.connect(self._browse_excel_startup)

        excel_startup_layout = QHBoxLayout()
        excel_startup_layout.addWidget(self.excel_startup_input)
        excel_startup_layout.addWidget(excel_browse_btn)
        wps_layout.addRow("Excel 模板目录:", excel_startup_layout)

        wps_group.setLayout(wps_layout)
        layout.addWidget(wps_group)

        # Chrome JS group
        chrome_group = QGroupBox("Chrome JS 配置")
        chrome_layout = QFormLayout()
        chrome_layout.setSpacing(10)

        self.chrome_path_input = QLineEdit()
        self.chrome_path_input.setPlaceholderText("Chrome 书签文件路径 (Bookmarks)")
        chrome_browse_btn = QPushButton("浏览...")
        chrome_browse_btn.clicked.connect(self._browse_chrome_path)
        chrome_auto_detect_btn = QPushButton("自动探测")
        chrome_auto_detect_btn.clicked.connect(self._auto_detect_chrome)

        chrome_path_layout = QHBoxLayout()
        chrome_path_layout.addWidget(self.chrome_path_input)
        chrome_path_layout.addWidget(chrome_browse_btn)
        chrome_path_layout.addWidget(chrome_auto_detect_btn)

        chrome_layout.addRow("Chrome 书签文件:", chrome_path_layout)
        chrome_group.setLayout(chrome_layout)
        layout.addWidget(chrome_group)

        # Add stretch
        layout.addStretch()
        self.setLayout(layout)

    # Browse handlers
    def _browse_chrome_path(self):
        """Open file dialog to select Chrome bookmarks file."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "选择 Chrome 书签文件",
            "",
            "Bookmarks 文件 (Bookmarks);;All Files (*)",
        )
        if path:
            self.chrome_path_input.setText(path)

    def _browse_word_startup(self):
        """Open folder dialog to select Word template directory."""
        path = QFileDialog.getExistingDirectory(
            self, "选择 Word 模板目录", ""
        )
        if path:
            self.word_startup_input.setText(path)

    def _browse_excel_startup(self):
        """Open folder dialog to select Excel template directory."""
        path = QFileDialog.getExistingDirectory(
            self, "选择 Excel 模板目录", ""
        )
        if path:
            self.excel_startup_input.setText(path)

    def _browse_scripts_dir(self):
        """Open folder dialog to select scripts directory."""
        path = QFileDialog.getExistingDirectory(self, "选择脚本存储目录", "")
        if path:
            self.scripts_dir_input.setText(path)

    # Auto-detect handlers
    def _auto_detect_chrome(self):
        """Auto-detect Chrome bookmarks path."""
        path = self.path_detection_service.detect_chrome_bookmarks_file()
        if path:
            self.chrome_path_input.setText(path)

    def save_config(self, config_service):
        """Save configuration to config service.

        Args:
            config_service: ConfigService instance
        """
        config_service.set("paths.scripts_dir", self.scripts_dir_input.text())
        config_service.set("paths.wps_word_startup", self.word_startup_input.text())
        config_service.set("paths.wps_excel_startup", self.excel_startup_input.text())
        config_service.set("paths.chrome_bookmarks", self.chrome_path_input.text())
        config_service.save()


class AboutTab(QWidget):
    """About tab with application information."""

    def __init__(self, parent=None):
        """Initialize the AboutTab.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        """Set up the AboutTab UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Application name
        title = QLabel("ScriptNexus")
        title.setFont(QFont("Microsoft YaHei", 20, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Subtitle / tagline
        subtitle = QLabel("办公脚本一站式管理平台")
        subtitle.setStyleSheet("color: #666; font-size: 13px;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        # Version
        version = QLabel("版本 1.0.0")
        version.setStyleSheet("color: #999; font-size: 11px;")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version)

        layout.addSpacing(16)

        # About story (scrollable)
        about_text = QTextEdit()
        about_text.setReadOnly(True)
        about_text.setFrameShape(QTextEdit.Shape.NoFrame)
        about_text.setStyleSheet("""
            QTextEdit {
                color: #333;
                font-size: 12px;
                background-color: #f9f9f9;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 12px;
            }
        """)
        about_text.setHtml(
            "<p style='line-height:1.7;'>"
            "诞生于<b>企业（）</b>内网环境，以 <b>vibe coding</b> 从零构建的 AI 辅助办公自动化工具。<br><br>"
            "作者是一名企业员工，<b>没有技术背景</b>。在 AI 浪潮下开始学习 vibe coding，"
            "ScriptNexus 是完成的<b>第一个复杂项目</b>——从内网办公场景的真实需求出发，"
            "逐步迭代为覆盖 Python 脚本、WPS 宏和 Chrome JS 书签的一站式管理平台。<br><br>"
            "目标是<b>逐步在内网搭建一个办公自动化的生态底座</b>，"
            "让更多同事借助 AI 降低重复性劳动的门槛。<br><br>"
            "当前支持 Windows，银行切换麒麟系统后将及时适配。"
            "</p>"
        )
        about_text.setFixedHeight(160)
        layout.addWidget(about_text)

        layout.addSpacing(12)

        # Features summary
        features_label = QLabel(
            "功能：Python 脚本管理 · WPS 宏 + Ribbon 部署 · Chrome JS 书签管理 · 导入导出 · 系统托盘"
        )
        features_label.setWordWrap(True)
        features_label.setStyleSheet("color: #555; font-size: 11px;")
        layout.addWidget(features_label)

        layout.addSpacing(16)

        # Runtime environment info
        env_text = (
            f"运行环境：\n"
            f"  - 操作系统：{platform.system()} {platform.release()}\n"
            f"  - Python：{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}\n"
            f"  - PyQt6：已加载"
        )
        env_info = QLabel(env_text)
        env_info.setWordWrap(True)
        env_info.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(env_info)

        layout.addStretch()
        self.setLayout(layout)
