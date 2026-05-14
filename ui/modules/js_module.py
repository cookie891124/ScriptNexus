"""JsModule - Chrome JS 脚本（bookmarklet）管理模块."""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget,
    QListWidgetItem, QTextEdit, QLabel, QDialog, QLineEdit,
    QMessageBox, QSplitter, QFrame, QComboBox, QFormLayout,
    QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class ScriptDialog(QDialog):
    """Dialog for creating or editing a Chrome JS bookmarklet."""

    def __init__(self, parent=None, script_data=None, existing_folders=None):
        super().__init__(parent)
        self.script_data = script_data
        self.is_edit_mode = script_data is not None
        self.existing_folders = existing_folders or []
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        self.setWindowTitle("编辑 Chrome JS脚本" if self.is_edit_mode else "新增 Chrome JS脚本")
        self.setMinimumSize(680, 520)
        self.setModal(True)

        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        # Name
        layout.addWidget(QLabel("脚本名称"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("例如：导出表格CSV、显示密码")
        self.name_input.setMinimumHeight(32)
        layout.addWidget(self.name_input)

        # Folder + Position row
        row = QHBoxLayout()
        row.setSpacing(12)

        folder_wrap = QVBoxLayout()
        folder_wrap.addWidget(QLabel("子文件夹（可选）"))
        self.folder_combo = QComboBox()
        self.folder_combo.setEditable(True)
        self.folder_combo.setMinimumHeight(32)
        self.folder_combo.setMinimumWidth(200)
        self.folder_combo.setPlaceholderText("留空 = 直接放在 JS Scripts")
        self.folder_combo.addItem("")  # empty = root
        for f in sorted(set(self.existing_folders)):
            if f:
                self.folder_combo.addItem(f)
        self.folder_combo.setCurrentIndex(0)
        folder_wrap.addWidget(self.folder_combo)
        row.addLayout(folder_wrap, 3)

        pos_wrap = QVBoxLayout()
        pos_wrap.addWidget(QLabel("排序"))
        self.position_input = QLineEdit()
        self.position_input.setPlaceholderText("越小越靠前")
        self.position_input.setFixedWidth(100)
        self.position_input.setMinimumHeight(32)
        pos_wrap.addWidget(self.position_input)
        row.addLayout(pos_wrap, 1)

        layout.addLayout(row)

        # URL (multi-line, below folder)
        layout.addWidget(QLabel("脚本 URL (bookmarklet 或远程地址)"))
        self.url_input = QTextEdit()
        self.url_input.setFont(QFont("Consolas", 10))
        self.url_input.setPlaceholderText("javascript:(function(){ /* your code */ })()")
        self.url_input.setMinimumHeight(120)
        self.url_input.setAcceptRichText(False)
        layout.addWidget(self.url_input, 1)

        # Tip
        tip = QLabel("Tip: bookmarklet 格式 javascript:(function(){...})()；支持 http/https/file 协议")
        tip.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(tip)

        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedWidth(100)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("保存")
        save_btn.setFixedWidth(100)
        save_btn.setDefault(True)
        save_btn.setStyleSheet("QPushButton { background-color: #0078D4; color: white; border: none; padding: 8px 16px; } QPushButton:hover { background-color: #006cbd; }")
        save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def _load_data(self):
        if self.is_edit_mode and self.script_data:
            self.name_input.setText(self.script_data.get("name", ""))
            self.url_input.setPlainText(self.script_data.get("url", ""))
            folder = self.script_data.get("parent_folder", "")
            idx = self.folder_combo.findText(folder)
            if idx >= 0:
                self.folder_combo.setCurrentIndex(idx)
            else:
                self.folder_combo.setEditText(folder)
            self.position_input.setText(str(self.script_data.get("position", 0)))

    def _on_save(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "警告", "请输入脚本名称")
            return

        url = self.url_input.toPlainText().strip()
        if not url:
            QMessageBox.warning(self, "警告", "请输入脚本 URL")
            return

        self.accept()

    def get_script_data(self):
        try:
            position = int(self.position_input.text().strip() or 0)
        except ValueError:
            position = 0

        return {
            "name": self.name_input.text().strip(),
            "url": self.url_input.toPlainText().strip(),
            "parent_folder": self.folder_combo.currentText().strip(),
            "position": position,
        }


class JsModule(QWidget):
    """Chrome JS 脚本管理模块（bookmarklet 部署）."""

    script_added = pyqtSignal()
    script_deleted = pyqtSignal()
    script_updated = pyqtSignal()

    def __init__(self, db_path: str, parent=None):
        super().__init__(parent)
        self.db_path = db_path

        from services.js_service import JsService
        self.js_service = JsService(db_path)

        self._setup_ui()
        self._refresh_list()

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        # ---- Title ----
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(2, 2, 2, 2)
        title_layout.setSpacing(10)

        title_label = QLabel("Chrome JS 脚本管理 [v0520]")
        title_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #333;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        layout.addLayout(title_layout, 0)  # stretch=0: don't expand

        # ---- Toolbar ----
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(4)
        toolbar_layout.setContentsMargins(2, 0, 2, 2)

        self.add_btn = QPushButton("+ 新增")
        self.add_btn.setFixedHeight(28)
        self.add_btn.setStyleSheet(self._btn_style("#107c10"))
        self.add_btn.clicked.connect(self._on_add_script)
        toolbar_layout.addWidget(self.add_btn)

        self.edit_btn = QPushButton("修改")
        self.edit_btn.setFixedHeight(28)
        self.edit_btn.setStyleSheet(self._btn_style("#0078D4"))
        self.edit_btn.clicked.connect(self._on_edit_script)
        toolbar_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("删除")
        self.delete_btn.setFixedHeight(28)
        self.delete_btn.setStyleSheet(self._btn_style("#d83b01"))
        self.delete_btn.clicked.connect(self._on_delete_script)
        toolbar_layout.addWidget(self.delete_btn)

        toolbar_layout.addSpacing(20)

        self.open_btn = QPushButton("在 Chrome 中打开")
        self.open_btn.setFixedHeight(28)
        self.open_btn.setStyleSheet(self._btn_style("#4285F4"))
        self.open_btn.clicked.connect(self._on_open_in_chrome)
        toolbar_layout.addWidget(self.open_btn)

        self.deploy_btn = QPushButton("部署到 Chrome")
        self.deploy_btn.setFixedHeight(28)
        self.deploy_btn.setStyleSheet(self._btn_style("#009900"))
        self.deploy_btn.clicked.connect(self._on_deploy_bookmarks)
        toolbar_layout.addWidget(self.deploy_btn)

        # Path label
        toolbar_layout.addStretch()
        self.path_label = QLabel("书签路径：未设置")
        self.path_label.setStyleSheet("color: #999; font-size: 11px;")
        toolbar_layout.addWidget(self.path_label)

        layout.addLayout(toolbar_layout, 0)  # stretch=0: don't expand

        # ---- Main content: splitter ----
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)

        # === Left: script list ===
        list_panel = QWidget()
        ll = QVBoxLayout()
        ll.setContentsMargins(0, 0, 0, 0)
        ll.setSpacing(0)

        list_hdr = QLabel("脚本列表")
        list_hdr.setStyleSheet("font-weight: bold; padding: 3px; background: #e8e8e8;")
        list_hdr.setFixedHeight(24)
        ll.addWidget(list_hdr)

        self.script_list = QListWidget()
        self.script_list.setAlternatingRowColors(True)
        self.script_list.itemSelectionChanged.connect(self._on_selection_changed)
        ll.addWidget(self.script_list)

        list_panel.setLayout(ll)

        # === Right: vertical split (details top / preview bottom) ===
        vsplit = QSplitter(Qt.Orientation.Vertical)
        vsplit.setHandleWidth(1)

        # -- Details panel --
        detail_panel = QWidget()
        dl = QVBoxLayout()
        dl.setContentsMargins(6, 4, 6, 4)
        dl.setSpacing(3)

        dl_hdr = QLabel("脚本信息")
        dl_hdr.setStyleSheet("font-weight: bold; padding: 3px; background: #e8e8e8;")
        dl_hdr.setFixedHeight(24)
        dl.addWidget(dl_hdr)

        self.detail_form = QFormLayout()
        self.detail_form.setSpacing(10)

        self.detail_name = QLabel("-")
        self.detail_url = QLabel("-")
        self.detail_url.setWordWrap(True)
        self.detail_url.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.detail_folder = QLabel("-")
        self.detail_pos = QLabel("-")

        self.detail_form.addRow("脚本名称:", self.detail_name)
        self.detail_form.addRow("URL:", self.detail_url)
        self.detail_form.addRow("书签文件夹:", self.detail_folder)
        self.detail_form.addRow("排序位置:", self.detail_pos)

        dl.addLayout(self.detail_form)
        dl.addStretch()
        detail_panel.setLayout(dl)

        # -- Preview panel --
        preview_panel = QWidget()
        pl = QVBoxLayout()
        pl.setContentsMargins(6, 4, 6, 4)
        pl.setSpacing(3)

        pl_hdr = QLabel("书签 JSON 预览")
        pl_hdr.setStyleSheet("font-weight: bold; padding: 3px; background: #e8e8e8;")
        pl_hdr.setFixedHeight(24)
        pl.addWidget(pl_hdr)

        self.json_preview = QTextEdit()
        self.json_preview.setFont(QFont("Consolas", 9))
        self.json_preview.setReadOnly(True)
        self.json_preview.setPlaceholderText('点击"部署到 Chrome"按钮查看生成的书签结构...')
        pl.addWidget(self.json_preview)

        preview_panel.setLayout(pl)

        vsplit.addWidget(detail_panel)
        vsplit.addWidget(preview_panel)
        vsplit.setStretchFactor(0, 2)
        vsplit.setStretchFactor(1, 3)

        splitter.addWidget(list_panel)
        splitter.addWidget(vsplit)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        layout.addWidget(splitter, 1)  # stretch=1: take remaining space
        self.setLayout(layout)

    def _btn_style(self, color):
        return f"""
            QPushButton {{ background-color: {color}; color: white; border: none;
                padding: 4px 14px; border-radius: 4px; font-size: 12px; }}
            QPushButton:hover {{ opacity: 0.9; }}
        """

    # ---- List & selection ----

    def _refresh_list(self):
        self.script_list.clear()
        scripts = self.js_service.get_all_scripts()
        for s in scripts:
            folder = s.get("parent_folder", "") or "JS Scripts"
            item = QListWidgetItem(f"{s['name']}  —  {folder}")
            item.setData(Qt.ItemDataRole.UserRole, s["id"])
            self.script_list.addItem(item)

    def _on_selection_changed(self):
        sel = self.script_list.selectedItems()
        if not sel:
            self._clear_details()
            return
        sid = sel[0].data(Qt.ItemDataRole.UserRole)
        if sid:
            script = self.js_service.get_script(sid)
            if script:
                self._show_details(script)

    def _clear_details(self):
        for w in [self.detail_name, self.detail_url, self.detail_folder, self.detail_pos]:
            w.setText("-")

    def _show_details(self, s):
        self.detail_name.setText(s.get("name", "-"))
        self.detail_url.setText(s.get("url", "-"))
        self.detail_folder.setText(s.get("parent_folder", "") or "JS Scripts")
        self.detail_pos.setText(str(s.get("position", 0)))

    # ---- CRUD ----

    def _on_add_script(self):
        folders = self._collect_folders()
        dlg = ScriptDialog(self, existing_folders=folders)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_script_data()
            self.js_service.add_script(name=data["name"], url=data["url"],
                                       parent_folder=data["parent_folder"],
                                       position=data["position"])
            self._refresh_list()
            self.script_added.emit()

    def _on_edit_script(self):
        sel = self.script_list.selectedItems()
        if not sel:
            QMessageBox.warning(self, "警告", "请选择要修改的脚本")
            return
        sid = sel[0].data(Qt.ItemDataRole.UserRole)
        if not sid:
            return
        script = self.js_service.get_script(sid)
        if not script:
            return

        folders = self._collect_folders()
        dlg = ScriptDialog(self, script_data=script, existing_folders=folders)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_script_data()
            self.js_service.update_script(sid, name=data["name"], url=data["url"],
                                          parent_folder=data["parent_folder"],
                                          position=data["position"])
            self._refresh_list()
            self.script_updated.emit()

    def _on_delete_script(self):
        sel = self.script_list.selectedItems()
        if not sel:
            return
        sid = sel[0].data(Qt.ItemDataRole.UserRole)
        if not sid:
            return
        reply = QMessageBox.question(self, "确认删除", "确定要删除选中的脚本吗？")
        if reply == QMessageBox.StandardButton.Yes:
            if self.js_service.delete_script(sid):
                self._refresh_list()
                self._clear_details()
                self.script_deleted.emit()

    def _collect_folders(self):
        """Gather distinct parent_folder values from all scripts."""
        folders = set()
        for s in self.js_service.get_all_scripts():
            f = s.get("parent_folder", "")
            if f:
                folders.add(f)
        return list(folders)

    # ---- Deploy ----

    def _on_deploy_bookmarks(self):
        if not self.js_service.chrome_path:
            QMessageBox.warning(self, "警告", "请先在全局设置中配置 Chrome 书签路径")
            return

        result = self.js_service.deploy_bookmarks()

        if result["success"]:
            if "preview" in result:
                self.json_preview.setPlainText(result["preview"])
            QMessageBox.information(self, "部署成功", result["message"])
        else:
            QMessageBox.warning(self, "部署失败", result["message"])

    # ---- Open in Chrome ----

    def _on_open_in_chrome(self):
        sel = self.script_list.selectedItems()
        if not sel:
            QMessageBox.warning(self, "警告", "请选择要打开的脚本")
            return
        sid = sel[0].data(Qt.ItemDataRole.UserRole)
        if not sid:
            return
        ok = self.js_service.open_in_chrome(sid)
        if not ok:
            QMessageBox.warning(self, "警告", "无法在 Chrome 中打开脚本")

    # ---- Global path (called by main_window) ----

    def set_chrome_path(self, path: str):
        self.js_service.set_chrome_path(path)
        if path:
            self.path_label.setText(f"书签路径：{path}")
            self.path_label.setStyleSheet("color: #107c10; font-size: 11px;")
        else:
            self.path_label.setText("书签路径：未设置")
            self.path_label.setStyleSheet("color: #aaa; font-size: 11px;")
