"""ImportDialog - Dialog for importing scripts and data with mode selection."""

import os
import json
import zipfile
import tempfile
import shutil

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QRadioButton, QLineEdit, QFileDialog, QMessageBox, QButtonGroup,
    QGroupBox, QTextEdit, QDialogButtonBox, QFrame,
)
from PyQt6.QtCore import Qt
from ui.theme import set_button_variant


class ImportDialog(QDialog):
    """Dialog for importing an .snx package with overwrite/append mode."""

    def __init__(self, scripts_dir: str = "", templates_dir: str = "",
                 db_path: str = "", parent=None):
        super().__init__(parent)
        self.scripts_dir = scripts_dir
        self.templates_dir = templates_dir
        self.db_path = db_path
        self.zip_path = ""
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("导入")
        self.setMinimumSize(580, 520)
        self.setModal(True)

        layout = QVBoxLayout()
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        # Header
        header = QLabel("导入 ScriptNexus 数据包")
        header.setStyleSheet("font-size: 19px; font-weight: 700; color: #202333;")
        layout.addWidget(header)

        # File selector
        file_label = QLabel("选择导入文件 (.snx):")
        file_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(file_label)

        file_row = QHBoxLayout()
        file_row.setSpacing(8)
        self.file_input = QLineEdit()
        self.file_input.setReadOnly(True)
        self.file_input.setStyleSheet("background: #f5f5f5;")
        file_row.addWidget(self.file_input)

        browse_btn = QPushButton("浏览...")
        browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(self._browse_file)
        file_row.addWidget(browse_btn)
        layout.addLayout(file_row)

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #ddd;")
        layout.addWidget(line)

        # Preview
        preview_label = QLabel("文件预览:")
        preview_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(preview_label)

        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(180)
        self.preview_text.setStyleSheet("background: #fafafa; font-size: 12px;")
        self.preview_text.setPlaceholderText("请先选择一个 .snx 文件...")
        layout.addWidget(self.preview_text)

        # Separator
        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.HLine)
        line2.setStyleSheet("color: #ddd;")
        layout.addWidget(line2)

        # Import mode
        mode_label = QLabel("导入模式:")
        mode_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(mode_label)

        mode_group = QGroupBox()
        mode_layout = QVBoxLayout()
        mode_layout.setSpacing(6)

        self.mode_group = QButtonGroup(self)
        self.overwrite_rb = QRadioButton("覆盖 — 清空现有数据，使用导入数据替换")
        self.append_rb = QRadioButton("新增 — 保留现有数据，追加导入数据（同名脚本覆盖）")
        self.append_rb.setChecked(True)

        self.mode_group.addButton(self.overwrite_rb, 1)
        self.mode_group.addButton(self.append_rb, 2)

        mode_layout.addWidget(self.overwrite_rb)
        mode_layout.addWidget(self.append_rb)
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)

        # Path handling note
        path_note = QLabel(
            "注意：导入的路径配置（脚本目录、模板目录、Chrome书签）\n"
            "如果当前计算机中不存在，将保留您当前的设置。"
        )
        path_note.setStyleSheet("color: #888; font-size: 11px;")
        path_note.setWordWrap(True)
        layout.addWidget(path_note)

        layout.addStretch()

        # Buttons
        btn_box = QDialogButtonBox()
        cancel_btn = btn_box.addButton("取消", QDialogButtonBox.ButtonRole.RejectRole)
        cancel_btn.clicked.connect(self.reject)
        import_btn = QPushButton("导入")
        set_button_variant(import_btn, "primary")
        import_btn.clicked.connect(self._on_import)
        btn_box.addButton(import_btn, QDialogButtonBox.ButtonRole.AcceptRole)
        layout.addWidget(btn_box)

        self.setLayout(layout)

    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择 ScriptNexus 导出文件", "",
            "ScriptNexus 文件 (*.snx);;All Files (*)"
        )
        if path:
            self.file_input.setText(path)
            self.zip_path = path
            self._update_preview()

    def _update_preview(self):
        if not self.zip_path or not os.path.exists(self.zip_path):
            return

        try:
            if not zipfile.is_zipfile(self.zip_path):
                self.preview_text.setPlainText("[错误] 不是有效的 .snx 文件")
                return

            with zipfile.ZipFile(self.zip_path, 'r') as zf:
                files = zf.namelist()

            # Check for metadata
            info_lines = []
            if 'metadata.json' in files:
                with zipfile.ZipFile(self.zip_path, 'r') as zf:
                    meta = json.loads(zf.read('metadata.json'))
                info_lines.append(f"导出时间: {meta.get('timestamp', '未知')}")
                info_lines.append(f"导出用户: {meta.get('username', '未知')}")
                modules = meta.get('modules', {})
                info_lines.append("")
                info_lines.append("包含模块:")
                for mod, data in modules.items():
                    mod_name = {'python': 'Python 脚本', 'wps': 'WPS JSA 脚本', 'js': 'Chrome JS 脚本'}.get(mod, mod)
                    items = [k for k, v in data.items() if v]
                    info_lines.append(f"  • {mod_name}: {', '.join(items) if items else '无'}")
            else:
                info_lines.append("[旧格式文件，无元数据]")
                info_lines.append("")

            # List files
            info_lines.append("")
            info_lines.append(f"文件数: {len(files)}")
            for f in sorted(files[:20]):
                info_lines.append(f"  {f}")
            if len(files) > 20:
                info_lines.append(f"  ... 及其他 {len(files) - 20} 个文件")

            self.preview_text.setPlainText('\n'.join(info_lines))

        except Exception as e:
            self.preview_text.setPlainText(f"[错误] 无法读取文件: {e}")

    def _on_import(self):
        if not self.zip_path:
            QMessageBox.warning(self, "警告", "请先选择导入文件")
            return
        if not os.path.exists(self.zip_path):
            QMessageBox.warning(self, "警告", f"文件不存在: {self.zip_path}")
            return
        self.accept()

    def get_import_options(self) -> dict:
        return {
            'zip_path': self.zip_path,
            'mode': 'overwrite' if self.overwrite_rb.isChecked() else 'merge',
        }
