"""ExportDialog - Dialog for exporting scripts and data with module selection."""

import os
import getpass
from datetime import datetime

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QCheckBox, QGroupBox, QLineEdit, QFileDialog, QMessageBox,
    QDialogButtonBox, QFrame,
)
from PyQt6.QtCore import Qt


class ExportDialog(QDialog):
    """Dialog for selecting modules and data to export."""

    def __init__(self, scripts_dir: str = "", templates_dir: str = "",
                 db_path: str = "", parent=None):
        super().__init__(parent)
        self.scripts_dir = scripts_dir
        self.templates_dir = templates_dir
        self.db_path = db_path
        self._setup_ui()
        self._update_file_name()

    def _setup_ui(self):
        self.setWindowTitle("导出")
        self.setMinimumSize(560, 520)
        self.setModal(True)

        layout = QVBoxLayout()
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        # Header
        header = QLabel("选择要导出的内容")
        header.setStyleSheet("font-size: 15px; font-weight: bold; color: #333;")
        layout.addWidget(header)

        hint = QLabel("勾选需要导出的模块和数据类型，未勾选的内容将不会被导出。")
        hint.setStyleSheet("color: #888; font-size: 12px;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        # Select all checkbox
        self.select_all_cb = QCheckBox("全选 / 取消全选")
        self.select_all_cb.setStyleSheet("font-weight: bold; font-size: 13px;")
        self.select_all_cb.stateChanged.connect(self._on_select_all)
        layout.addWidget(self.select_all_cb)

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #ddd;")
        layout.addWidget(line)

        # --- Python group ---
        self.py_group = QCheckBox("Python 脚本")
        self.py_group.setStyleSheet("font-weight: bold; font-size: 13px;")
        self.py_group.stateChanged.connect(self._on_group_changed)
        layout.addWidget(self.py_group)

        self.py_db_cb = QCheckBox("    脚本数据（数据库）")
        self.py_files_cb = QCheckBox("    脚本文件目录")
        self.py_db_cb.setChecked(True)
        self.py_files_cb.setChecked(True)
        layout.addWidget(self.py_db_cb)
        layout.addWidget(self.py_files_cb)

        # --- WPS group ---
        self.wps_group = QCheckBox("WPS JSA 脚本")
        self.wps_group.setStyleSheet("font-weight: bold; font-size: 13px;")
        self.wps_group.stateChanged.connect(self._on_group_changed)
        layout.addWidget(self.wps_group)

        self.wps_db_cb = QCheckBox("    脚本数据（数据库）")
        self.wps_ribbon_cb = QCheckBox("    功能区结构（数据库）")
        self.wps_templates_cb = QCheckBox("    模板文件目录")
        self.wps_db_cb.setChecked(True)
        self.wps_ribbon_cb.setChecked(True)
        self.wps_templates_cb.setChecked(True)
        layout.addWidget(self.wps_db_cb)
        layout.addWidget(self.wps_ribbon_cb)
        layout.addWidget(self.wps_templates_cb)

        # --- Chrome JS group ---
        self.js_group = QCheckBox("Chrome JS 脚本")
        self.js_group.setStyleSheet("font-weight: bold; font-size: 13px;")
        self.js_group.stateChanged.connect(self._on_group_changed)
        layout.addWidget(self.js_group)

        self.js_db_cb = QCheckBox("    脚本数据（数据库）")
        self.js_db_cb.setChecked(True)
        layout.addWidget(self.js_db_cb)

        # Separator
        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.HLine)
        line2.setStyleSheet("color: #ddd;")
        layout.addWidget(line2)

        # Output path
        path_label = QLabel("导出路径:")
        path_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(path_label)

        path_row = QHBoxLayout()
        path_row.setSpacing(8)
        self.path_input = QLineEdit()
        self.path_input.setReadOnly(True)
        self.path_input.setStyleSheet("background: #f5f5f5;")
        path_row.addWidget(self.path_input)

        browse_btn = QPushButton("浏览...")
        browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(self._browse_output_dir)
        path_row.addWidget(browse_btn)
        layout.addLayout(path_row)

        # File name
        name_row = QHBoxLayout()
        name_row.setSpacing(8)
        name_label = QLabel("文件名:")
        name_label.setFixedWidth(60)
        name_row.addWidget(name_label)
        self.name_input = QLineEdit()
        name_row.addWidget(self.name_input)
        layout.addLayout(name_row)

        layout.addStretch()

        # Buttons
        btn_box = QDialogButtonBox()
        cancel_btn = btn_box.addButton("取消", QDialogButtonBox.ButtonRole.RejectRole)
        cancel_btn.clicked.connect(self.reject)
        export_btn = QPushButton("导出")
        export_btn.setStyleSheet("QPushButton { background-color: #0078D4; color: white; border: none; padding: 8px 20px; border-radius: 4px; } QPushButton:hover { background-color: #006cbd; }")
        export_btn.clicked.connect(self._on_export)
        btn_box.addButton(export_btn, QDialogButtonBox.ButtonRole.AcceptRole)
        layout.addWidget(btn_box)

        self.setLayout(layout)

    def _on_select_all(self, state):
        checked = state == Qt.CheckState.Checked.value
        for group in [self.py_group, self.wps_group, self.js_group]:
            group.setChecked(checked)
        for cb in [self.py_db_cb, self.py_files_cb,
                   self.wps_db_cb, self.wps_ribbon_cb, self.wps_templates_cb,
                   self.js_db_cb]:
            cb.setChecked(checked)

    def _on_group_changed(self):
        """When a group checkbox changes, update its children."""
        for group, children in [
            (self.py_group, [self.py_db_cb, self.py_files_cb]),
            (self.wps_group, [self.wps_db_cb, self.wps_ribbon_cb, self.wps_templates_cb]),
            (self.js_group, [self.js_db_cb]),
        ]:
            if group.isChecked():
                for c in children:
                    c.setChecked(True)
            else:
                for c in children:
                    c.setChecked(False)

    def _update_file_name(self):
        username = getpass.getuser()
        now = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_name = f"{username}_{now}.snx"
        if not self.name_input.text():
            self.name_input.setText(default_name)
        if not self.path_input.text():
            self.path_input.setText(os.path.expanduser("~\\Desktop"))

    def _browse_output_dir(self):
        path = QFileDialog.getExistingDirectory(self, "选择导出目录", self.path_input.text())
        if path:
            self.path_input.setText(path)
            self._update_file_name()

    def _on_export(self):
        if not self.path_input.text().strip():
            QMessageBox.warning(self, "警告", "请选择导出目录")
            return
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "警告", "请输入文件名")
            return

        # Ensure .snx extension
        name = self.name_input.text().strip()
        if not name.endswith('.snx'):
            name += '.snx'

        self.output_path = os.path.join(self.path_input.text().strip(), name)

        if os.path.exists(self.output_path):
            reply = QMessageBox.question(
                self, "确认覆盖", f"文件已存在:\n{self.output_path}\n\n是否覆盖?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return

        self.accept()

    def get_selections(self) -> dict:
        return {
            'python': {
                'db': self.py_db_cb.isChecked(),
                'files': self.py_files_cb.isChecked(),
            },
            'wps': {
                'db': self.wps_db_cb.isChecked(),
                'ribbon': self.wps_ribbon_cb.isChecked(),
                'templates': self.wps_templates_cb.isChecked(),
            },
            'js': {
                'db': self.js_db_cb.isChecked(),
            },
            'output_path': self.output_path,
        }
