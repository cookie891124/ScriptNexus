"""JsModule - JS script module with Chrome bookmark integration."""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget,
    QListWidgetItem, QTextEdit, QLabel, QDialog, QLineEdit,
    QMessageBox, QSplitter, QFrame, QComboBox, QFormLayout,
    QGroupBox, QTabWidget, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class ScriptDialog(QDialog):
    """Dialog for creating or editing a JS script."""

    def __init__(self, parent=None, script_data=None):
        """Initialize the script dialog.

        Args:
            parent: Parent widget
            script_data: Existing script data for edit mode, None for create mode
        """
        super().__init__(parent)
        self.script_data = script_data
        self.is_edit_mode = script_data is not None
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("编辑 JS 脚本" if self.is_edit_mode else "新增 JS 脚本")
        self.setMinimumSize(650, 550)
        self.setModal(True)

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Name field
        name_layout = QHBoxLayout()
        name_label = QLabel("脚本名称:")
        name_label.setFixedWidth(100)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("请输入脚本名称")
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)

        # URL field
        url_layout = QHBoxLayout()
        url_label = QLabel("脚本 URL:")
        url_label.setFixedWidth(100)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://example.com/script.js")
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        layout.addLayout(url_layout)

        # Parent folder field
        folder_layout = QHBoxLayout()
        folder_label = QLabel("书签文件夹:")
        folder_label.setFixedWidth(100)
        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText("例如：MyScripts（留空则直接放在书签栏）")
        folder_layout.addWidget(folder_label)
        folder_layout.addWidget(self.folder_input)
        layout.addLayout(folder_layout)

        # Position field
        position_layout = QHBoxLayout()
        position_label = QLabel("排序位置:")
        position_label.setFixedWidth(100)
        self.position_input = QLineEdit()
        self.position_input.setPlaceholderText("数字，越小越靠前")
        self.position_input.setFixedWidth(200)
        position_layout.addWidget(position_label)
        position_layout.addWidget(self.position_input)
        position_layout.addStretch()
        layout.addLayout(position_layout)

        # Code editor (for inline JS code)
        code_label = QLabel("JavaScript 代码 (可选):")
        layout.addWidget(code_label)

        self.code_editor = QTextEdit()
        self.code_editor.setFont(QFont("Consolas", 10))
        self.code_editor.setPlaceholderText("请输入 JavaScript 代码...（如果通过 URL 加载则留空）")
        layout.addWidget(self.code_editor)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setFixedWidth(100)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        self.save_btn = QPushButton("保存")
        self.save_btn.setFixedWidth(100)
        self.save_btn.setDefault(True)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078D4;
                color: white;
                border: none;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #006cbd;
            }
        """)
        self.save_btn.clicked.connect(self._on_save)
        button_layout.addWidget(self.save_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def _load_data(self):
        """Load existing script data for edit mode."""
        if self.is_edit_mode and self.script_data:
            self.name_input.setText(self.script_data.get("name", ""))
            self.url_input.setText(self.script_data.get("url", ""))
            self.folder_input.setText(self.script_data.get("parent_folder", ""))
            self.position_input.setText(str(self.script_data.get("position", 0)))

    def _on_save(self):
        """Handle save button click."""
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "警告", "请输入脚本名称")
            return

        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "警告", "请输入脚本 URL")
            return

        # Validate URL format (basic check)
        if not url.startswith(("http://", "https://", "file://")):
            reply = QMessageBox.question(
                self,
                "URL 格式警告",
                "URL 格式可能不正确，确定要继续吗？\n\nURL 应以 http://, https:// 或 file:// 开头",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        self.accept()

    def get_script_data(self):
        """Get the script data from the dialog.

        Returns:
            Dictionary with script fields
        """
        try:
            position = int(self.position_input.text().strip() or 0)
        except ValueError:
            position = 0

        return {
            "name": self.name_input.text().strip(),
            "url": self.url_input.text().strip(),
            "parent_folder": self.folder_input.text().strip(),
            "position": position
        }


class JsModule(QWidget):
    """JS script management module with Chrome bookmark integration.

    Features:
        - QListWidget for script list
        - URL/Code editor
        - Bookmark folder input
        - Buttons: Add, Edit, Delete, Open in Chrome, Generate Bookmarks, Deploy
    """

    # Signals
    script_added = pyqtSignal()
    script_deleted = pyqtSignal()
    script_updated = pyqtSignal()

    def __init__(self, db_path: str, parent=None):
        """Initialize the JS module.

        Args:
            db_path: Path to the SQLite database
            parent: Parent widget
        """
        super().__init__(parent)
        self.db_path = db_path

        # Initialize service
        from services.js_service import JsService
        self.js_service = JsService(db_path)

        self._setup_ui()
        self._refresh_list()

    def _setup_ui(self):
        """Set up the module UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Title (compact with toolbar)
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(10)

        title_label = QLabel("JS 脚本管理")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #333;
                padding: 5px 10px;
                background-color: #f0f0f0;
                border-radius: 4px;
            }
        """)
        title_label.setFixedHeight(35)
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        layout.addLayout(title_layout)

        # Toolbar
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(8)
        toolbar_layout.setContentsMargins(0, 0, 0, 5)

        self.add_btn = QPushButton("+ 新增")
        self.add_btn.setFixedHeight(35)
        self.add_btn.setStyleSheet(self._get_button_style("#107c10"))
        self.add_btn.clicked.connect(self._on_add_script)
        toolbar_layout.addWidget(self.add_btn)

        self.edit_btn = QPushButton("修改")
        self.edit_btn.setFixedHeight(35)
        self.edit_btn.setStyleSheet(self._get_button_style("#0078D4"))
        self.edit_btn.clicked.connect(self._on_edit_script)
        toolbar_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("删除")
        self.delete_btn.setFixedHeight(35)
        self.delete_btn.setStyleSheet(self._get_button_style("#d83b01"))
        self.delete_btn.clicked.connect(self._on_delete_script)
        toolbar_layout.addWidget(self.delete_btn)

        toolbar_layout.addSpacing(20)

        self.open_chrome_btn = QPushButton("在 Chrome 中打开")
        self.open_chrome_btn.setFixedHeight(35)
        self.open_chrome_btn.setStyleSheet(self._get_button_style("#4285F4"))
        self.open_chrome_btn.clicked.connect(self._on_open_in_chrome)
        toolbar_layout.addWidget(self.open_chrome_btn)

        self.generate_bookmarks_btn = QPushButton("生成书签 JSON")
        self.generate_bookmarks_btn.setFixedHeight(35)
        self.generate_bookmarks_btn.setStyleSheet(self._get_button_style("#8764b8"))
        self.generate_bookmarks_btn.clicked.connect(self._on_generate_bookmarks)
        toolbar_layout.addWidget(self.generate_bookmarks_btn)

        self.deploy_bookmarks_btn = QPushButton("部署到 Chrome")
        self.deploy_bookmarks_btn.setFixedHeight(35)
        self.deploy_bookmarks_btn.setStyleSheet(self._get_button_style("#009900"))
        self.deploy_bookmarks_btn.clicked.connect(self._on_deploy_bookmarks)
        toolbar_layout.addWidget(self.deploy_bookmarks_btn)

        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)

        # Chrome path info (compact)
        path_info_layout = QHBoxLayout()
        path_info_layout.setSpacing(5)
        path_info_layout.setContentsMargins(0, 0, 0, 5)

        path_label = QLabel("Chrome 书签路径:")
        path_label.setStyleSheet("QLabel { font-weight: bold; color: #555; }")
        path_info_layout.addWidget(path_label)

        self.chrome_path_label = QLabel("未设置")
        self.chrome_path_label.setStyleSheet("color: #666; padding: 3px 8px; background-color: #f5f5f5; border-radius: 3px;")
        path_info_layout.addWidget(self.chrome_path_label)

        self.set_path_btn = QPushButton("设置路径")
        self.set_path_btn.setFixedHeight(28)
        self.set_path_btn.setStyleSheet(self._get_button_style("#666666"))
        self.set_path_btn.clicked.connect(self._on_set_chrome_path)
        path_info_layout.addWidget(self.set_path_btn)

        path_info_layout.addStretch()
        layout.addLayout(path_info_layout)

        # Main content area with splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel - Script list
        list_panel = QFrame()
        list_layout = QVBoxLayout()
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(3)

        list_label = QLabel("脚本列表")
        list_label.setStyleSheet("QLabel { font-weight: bold; padding: 3px; background-color: #e8e8e8; }")
        list_label.setFixedHeight(25)
        list_layout.addWidget(list_label)

        self.script_list = QListWidget()
        self.script_list.setAlternatingRowColors(True)
        self.script_list.itemSelectionChanged.connect(self._on_list_selection_changed)
        list_layout.addWidget(self.script_list)

        list_panel.setLayout(list_layout)

        # Right panel - Script details
        editor_panel = QFrame()
        editor_layout = QVBoxLayout()
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.setSpacing(3)

        # Tab widget for details and preview
        self.tab_widget = QTabWidget()

        # Script details tab
        details_widget = QWidget()
        details_vbox = QVBoxLayout()
        details_vbox.setContentsMargins(10, 10, 10, 10)
        details_vbox.setSpacing(3)

        # Script info form
        details_title = QLabel("脚本信息")
        details_title.setStyleSheet("QLabel { font-weight: bold; padding: 3px; background-color: #e8e8e8; }")
        details_title.setFixedHeight(25)
        details_vbox.addWidget(details_title)

        self.details_form = QFormLayout()
        self.details_form.setSpacing(10)

        self.details_name = QLabel("-")
        self.details_url = QLabel("-")
        self.details_folder = QLabel("-")
        self.details_position = QLabel("-")

        self.details_form.addRow("脚本名称:", self.details_name)
        self.details_form.addRow("URL:", self.details_url)
        self.details_form.addRow("书签文件夹:", self.details_folder)
        self.details_form.addRow("排序位置:", self.details_position)

        details_vbox.addLayout(self.details_form)
        details_vbox.addStretch()
        details_widget.setLayout(details_vbox)
        self.tab_widget.addTab(details_widget, "脚本详情")

        # Bookmarks preview tab
        preview_widget = QWidget()
        preview_vbox = QVBoxLayout()
        preview_vbox.setContentsMargins(5, 5, 5, 5)
        preview_vbox.setSpacing(3)

        preview_label = QLabel("书签 JSON 预览")
        preview_label.setStyleSheet("QLabel { font-weight: bold; padding: 3px; background-color: #e8e8e8; }")
        preview_label.setFixedHeight(25)
        preview_vbox.addWidget(preview_label)

        self.json_preview = QTextEdit()
        self.json_preview.setFont(QFont("Consolas", 9))
        self.json_preview.setReadOnly(True)
        self.json_preview.setPlaceholderText('点击"生成书签 JSON"按钮查看生成的书签结构...')
        preview_vbox.addWidget(self.json_preview)

        preview_widget.setLayout(preview_vbox)
        self.tab_widget.addTab(preview_widget, "书签预览")

        editor_layout.addWidget(self.tab_widget)
        editor_panel.setLayout(editor_layout)

        splitter.addWidget(list_panel)
        splitter.addWidget(editor_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        layout.addWidget(splitter)

        self.setLayout(layout)

    def _get_button_style(self, color):
        """Get button stylesheet for given color.

        Args:
            color: Button background color (hex)

        Returns:
            CSS stylesheet string
        """
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                opacity: 0.9;
            }}
            QPushButton:pressed {{
                opacity: 0.8;
            }}
        """

    def _refresh_list(self):
        """Refresh the script list."""
        self.script_list.clear()

        scripts = self.js_service.get_all_scripts()
        for script in scripts:
            folder = script.get("parent_folder", "") or "书签栏"
            item = QListWidgetItem(f"{script['name']} ({folder})")
            item.setData(Qt.ItemDataRole.UserRole, script["id"])
            self.script_list.addItem(item)

    def _on_list_selection_changed(self):
        """Handle list selection change."""
        selected_items = self.script_list.selectedItems()
        if not selected_items:
            self._clear_details()
            return

        item = selected_items[0]
        script_id = item.data(Qt.ItemDataRole.UserRole)

        if script_id:
            script = self.js_service.get_script(script_id)
            if script:
                self._update_details(script)

    def _clear_details(self):
        """Clear the details display."""
        self.details_name.setText("-")
        self.details_url.setText("-")
        self.details_folder.setText("-")
        self.details_position.setText("-")

    def _update_details(self, script):
        """Update the details display with script data.

        Args:
            script: Script data dictionary
        """
        self.details_name.setText(script.get("name", "-"))
        self.details_url.setText(script.get("url", "-"))
        self.details_folder.setText(script.get("parent_folder", "") or "-")
        self.details_position.setText(str(script.get("position", 0)))

    def _on_add_script(self):
        """Handle add script button click."""
        dialog = ScriptDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_script_data()
            self.js_service.add_script(
                name=data["name"],
                url=data["url"],
                parent_folder=data["parent_folder"],
                position=data["position"]
            )
            self._refresh_list()
            self.script_added.emit()
            QMessageBox.information(self, "成功", "JS 脚本已添加")

    def _on_edit_script(self):
        """Handle edit script button click."""
        selected_items = self.script_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请选择要修改的脚本")
            return

        item = selected_items[0]
        script_id = item.data(Qt.ItemDataRole.UserRole)

        if not script_id:
            QMessageBox.warning(self, "警告", "请选择有效的脚本")
            return

        script = self.js_service.get_script(script_id)
        if not script:
            QMessageBox.warning(self, "警告", "脚本不存在")
            return

        dialog = ScriptDialog(self, script_data=script)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_script_data()
            self.js_service.update_script(
                script_id=script_id,
                name=data["name"],
                url=data["url"],
                parent_folder=data["parent_folder"],
                position=data["position"]
            )
            self._refresh_list()
            self.script_updated.emit()
            QMessageBox.information(self, "成功", "脚本已更新")

    def _on_delete_script(self):
        """Handle delete script button click."""
        selected_items = self.script_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请选择要删除的脚本")
            return

        item = selected_items[0]
        script_id = item.data(Qt.ItemDataRole.UserRole)

        if not script_id:
            QMessageBox.warning(self, "警告", "请选择有效的脚本")
            return

        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "确认删除",
            "确定要删除选中的脚本吗？此操作不可恢复。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.js_service.delete_script(script_id):
                self._refresh_list()
                self._clear_details()
                self.script_deleted.emit()
                QMessageBox.information(self, "成功", "脚本已删除")

    def _on_open_in_chrome(self):
        """Handle open in Chrome button click."""
        selected_items = self.script_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请选择要打开的脚本")
            return

        item = selected_items[0]
        script_id = item.data(Qt.ItemDataRole.UserRole)

        if not script_id:
            QMessageBox.warning(self, "警告", "请选择有效的脚本")
            return

        result = self.js_service.open_in_chrome(script_id)
        if not result:
            QMessageBox.warning(self, "警告", "无法在 Chrome 中打开脚本")

    def _on_generate_bookmarks(self):
        """Handle generate bookmarks button click."""
        import json
        bookmarks = self.js_service.generate_bookmarks_json()
        json_str = json.dumps(bookmarks, indent=2, ensure_ascii=False)
        self.json_preview.setPlainText(json_str)
        self.tab_widget.setCurrentIndex(1)  # Switch to preview tab

    def _on_deploy_bookmarks(self):
        """Handle deploy bookmarks button click."""
        if not self.js_service.chrome_path:
            QMessageBox.warning(
                self,
                "警告",
                "请先设置 Chrome 书签文件路径"
            )
            return

        result = self.js_service.deploy_bookmarks()
        if result:
            QMessageBox.information(
                self,
                "部署成功",
                f"书签已部署到:\n{self.js_service.chrome_path}\n\n请重启 Chrome 浏览器以查看更改。"
            )
        else:
            QMessageBox.warning(
                self,
                "部署失败",
                "部署书签失败，请检查路径设置"
            )

    def _on_set_chrome_path(self):
        """Handle set Chrome path button click."""
        from PyQt6.QtWidgets import QFileDialog

        # Default Chrome paths for Windows
        default_paths = [
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data"),
            os.path.expandvars(r"%APPDATA%\Google\Chrome\User Data"),
        ]

        # Try to find existing Chrome path
        initial_dir = None
        for path in default_paths:
            if os.path.exists(path):
                initial_dir = path
                break

        # Open folder dialog
        path = QFileDialog.getExistingDirectory(
            self,
            "选择 Chrome User Data 目录",
            initial_dir or "",
            QFileDialog.Option.ShowDirsOnly
        )

        if path:
            self.js_service.set_chrome_path(path)
            self.chrome_path_label.setText(path)
            self.chrome_path_label.setStyleSheet("color: #107c10;")

    def set_chrome_path(self, path: str):
        """Set the Chrome bookmarks path for JsService.

        Args:
            path: Path to the Chrome user data directory
        """
        self.js_service.set_chrome_path(path)
        self.chrome_path_label.setText(path)
        self.chrome_path_label.setStyleSheet("color: #107c10;")
