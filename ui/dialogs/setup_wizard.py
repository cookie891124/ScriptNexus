"""SetupWizard - First-run configuration wizard for the script manager."""

import os
from PyQt6.QtWidgets import (
    QWizard,
    QWizardPage,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QGroupBox,
    QFormLayout,
    QSpacerItem,
    QSizePolicy,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class SetupWizard(QWizard):
    """First-run configuration wizard.

    Pages:
        1. WelcomePage - Welcome message with option to skip
        2. PathsPage - Configure Chrome and WPS paths
        3. FinishPage - Completion message
    """

    def __init__(self, path_detection_service, config_service, parent=None):
        """Initialize the SetupWizard.

        Args:
            path_detection_service: PathDetectionService instance for auto-detection
            config_service: ConfigService instance for saving configuration
            parent: Parent widget
        """
        super().__init__(parent)
        self.path_detection_service = path_detection_service
        self.config_service = config_service

        self.setWindowTitle("首次启动向导 - 配置")
        self.setMinimumSize(600, 450)
        self.setModal(True)

        # Add pages
        self.addPage(WelcomePage(self))
        self.addPage(PathsPage(self, path_detection_service))
        self.addPage(FinishPage(self))

        # Set wizard style
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setOption(QWizard.WizardOption.NoBackButtonOnStartPage, True)
        self.setOption(QWizard.WizardOption.NoCancelButton, False)

        # Connect finish signal
        self.accepted.connect(self._on_finished)

    def _on_finished(self):
        """Handle wizard completion."""
        # Configuration is saved by PathsPage
        pass


class WelcomePage(QWizardPage):
    """Welcome page for the setup wizard."""

    def __init__(self, parent=None):
        """Initialize the WelcomePage.

        Args:
            parent: Parent QWizard
        """
        super().__init__(parent)
        self.setTitle("欢迎")
        self._setup_ui()

    def _setup_ui(self):
        """Set up the WelcomePage UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(15)

        # Welcome message
        welcome_label = QLabel("欢迎使用脚本管理器！")
        welcome_label.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(welcome_label)

        # Spacer
        layout.addSpacing(20)

        # Description
        description = QLabel(
            "本向导将帮助您完成首次启动配置，包括：\n\n"
            "  - 配置 Chrome 书签文件路径\n"
            "  - 配置 WPS Word 自启动目录\n"
            "  - 配置 WPS Excel 自启动目录\n\n"
            '如果您想稍后配置，可以点击"取消"按钮跳过此向导。'
        )
        description.setWordWrap(True)
        description.setStyleSheet("QLabel { font-size: 13px; color: #333; line-height: 1.8; }")
        layout.addWidget(description)

        # Spacer
        layout.addSpacing(20)

        # Note
        note_label = QLabel("提示：所有配置都可以在设置中随时修改。")
        note_label.setStyleSheet("QLabel { font-size: 12px; color: #666; font-style: italic; }")
        note_label.setWordWrap(True)
        layout.addWidget(note_label)

        layout.addStretch()

        self.setLayout(layout)

    def nextId(self):
        """Return the next page ID."""
        return 1


class PathsPage(QWizardPage):
    """Paths configuration page for Chrome and WPS."""

    def __init__(self, parent, path_detection_service):
        """Initialize the PathsPage.

        Args:
            parent: Parent QWizard
            path_detection_service: PathDetectionService instance for auto-detection
        """
        super().__init__(parent)
        self.path_detection_service = path_detection_service
        self.setTitle("路径配置")
        self.setSubTitle("请配置以下路径（已自动探测默认值，可手动修改）")
        self._setup_ui()

    @property
    def config_service(self):
        """Get config_service from parent wizard."""
        return self.wizard().config_service

    def _setup_ui(self):
        """Set up the PathsPage UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(15)

        # Chrome bookmarks group
        chrome_group = self._create_chrome_group()
        layout.addWidget(chrome_group)

        # WPS group
        wps_group = self._create_wps_group()
        layout.addWidget(wps_group)

        self.setLayout(layout)

    def _create_chrome_group(self):
        """Create Chrome bookmarks configuration group.

        Returns:
            QGroupBox containing Chrome configuration
        """
        group = QGroupBox("Chrome 书签文件路径")
        layout = QFormLayout()
        layout.setSpacing(10)

        # Chrome bookmarks path
        self.chrome_bookmarks_edit = QLineEdit()
        self.chrome_bookmarks_edit.setPlaceholderText("Chrome 书签文件路径")
        self.chrome_bookmarks_edit.setMinimumWidth(350)
        # Auto-detect and set default
        detected_path = self.path_detection_service.detect_chrome_bookmarks_file()
        self.chrome_bookmarks_edit.setText(detected_path)

        browse_chrome_btn = QPushButton("浏览...")
        browse_chrome_btn.setFixedWidth(70)
        browse_chrome_btn.clicked.connect(self._browse_chrome_bookmarks)

        chrome_layout = QHBoxLayout()
        chrome_layout.addWidget(self.chrome_bookmarks_edit)
        chrome_layout.addWidget(browse_chrome_btn)

        layout.addRow("书签文件:", chrome_layout)
        group.setLayout(layout)
        return group

    def _create_wps_group(self):
        """Create WPS startup directories configuration group.

        Returns:
            QGroupBox containing WPS configuration
        """
        group = QGroupBox("WPS 自启动目录")
        layout = QFormLayout()
        layout.setSpacing(10)

        # WPS Word startup path
        self.wps_word_edit = QLineEdit()
        self.wps_word_edit.setPlaceholderText("WPS Word 自启动目录")
        self.wps_word_edit.setMinimumWidth(350)
        # Auto-detect and set default
        detected_word_path = self.path_detection_service.detect_wps_word_startup()
        self.wps_word_edit.setText(detected_word_path)

        browse_word_btn = QPushButton("浏览...")
        browse_word_btn.setFixedWidth(70)
        browse_word_btn.clicked.connect(self._browse_wps_word)

        word_layout = QHBoxLayout()
        word_layout.addWidget(self.wps_word_edit)
        word_layout.addWidget(browse_word_btn)

        layout.addRow("Word 启动:", word_layout)

        # WPS Excel startup path
        self.wps_excel_edit = QLineEdit()
        self.wps_excel_edit.setPlaceholderText("WPS Excel 自启动目录")
        self.wps_excel_edit.setMinimumWidth(350)
        # Auto-detect and set default
        detected_excel_path = self.path_detection_service.detect_wps_excel_startup()
        self.wps_excel_edit.setText(detected_excel_path)

        browse_excel_btn = QPushButton("浏览...")
        browse_excel_btn.setFixedWidth(70)
        browse_excel_btn.clicked.connect(self._browse_wps_excel)

        excel_layout = QHBoxLayout()
        excel_layout.addWidget(self.wps_excel_edit)
        excel_layout.addWidget(browse_excel_btn)

        layout.addRow("Excel 启动:", excel_layout)
        group.setLayout(layout)
        return group

    def _browse_chrome_bookmarks(self):
        """Open file dialog to browse for Chrome bookmarks file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择 Chrome 书签文件",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        if file_path:
            self.chrome_bookmarks_edit.setText(file_path)

    def _browse_wps_word(self):
        """Open directory dialog to browse for WPS Word startup directory."""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "选择 WPS Word 自启动目录",
            ""
        )
        if dir_path:
            self.wps_word_edit.setText(dir_path)

    def _browse_wps_excel(self):
        """Open directory dialog to browse for WPS Excel startup directory."""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "选择 WPS Excel 自启动目录",
            ""
        )
        if dir_path:
            self.wps_excel_edit.setText(dir_path)

    def validatePage(self):
        """Validate the page before proceeding.

        Returns:
            True if validation passes, False otherwise
        """
        # Validate Chrome bookmarks path
        chrome_path = self.chrome_bookmarks_edit.text().strip()
        if not chrome_path:
            self._show_error("Chrome 书签文件路径不能为空")
            return False

        # Validate WPS Word startup path
        word_path = self.wps_word_edit.text().strip()
        if not word_path:
            self._show_error("WPS Word 自启动目录不能为空")
            return False

        # Validate WPS Excel startup path
        excel_path = self.wps_excel_edit.text().strip()
        if not excel_path:
            self._show_error("WPS Excel 自启动目录不能为空")
            return False

        # Save configuration
        self._save_configuration()
        return True

    def _save_configuration(self):
        """Save the configuration to config service."""
        self.config_service.set("paths.chrome_bookmarks", self.chrome_bookmarks_edit.text().strip())
        self.config_service.set("paths.wps_word_startup", self.wps_word_edit.text().strip())
        self.config_service.set("paths.wps_excel_startup", self.wps_excel_edit.text().strip())
        self.config_service.save()

    def _show_error(self, message):
        """Show an error message.

        Args:
            message: Error message to display
        """
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.warning(self, "警告", message)


class FinishPage(QWizardPage):
    """Finish page for the setup wizard."""

    def __init__(self, parent=None):
        """Initialize the FinishPage.

        Args:
            parent: Parent QWizard
        """
        super().__init__(parent)
        self.setTitle("完成")
        self._setup_ui()

    def _setup_ui(self):
        """Set up the FinishPage UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(15)

        # Success icon (using text)
        success_label = QLabel("✓")
        success_label.setFont(QFont("Segoe UI Symbol", 48, QFont.Weight.Bold))
        success_label.setStyleSheet("QLabel { color: #107C10; }")
        success_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(success_label)

        # Success message
        success_message = QLabel("配置已完成！")
        success_message.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        success_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(success_message)

        # Spacer
        layout.addSpacing(20)

        # Description
        description = QLabel(
            "恭喜！您已完成首次启动配置。\n\n"
            "现在可以开始使用脚本管理器的全部功能了。\n"
            "如有需要，可以随时在设置中修改配置。"
        )
        description.setWordWrap(True)
        description.setStyleSheet("QLabel { font-size: 13px; color: #333; line-height: 1.8; }")
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(description)

        layout.addStretch()

        self.setLayout(layout)

    def isFinalPage(self):
        """Indicate this is the final page.

        Returns:
            True to indicate this is the final page
        """
        return True
