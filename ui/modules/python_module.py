"""PythonModule - Python script management module with tree view and code editor."""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTreeWidget,
    QTreeWidgetItem, QTextEdit, QLabel, QDialog, QLineEdit,
    QMessageBox, QSplitter, QFrame, QToolBar, QFileDialog, QMenu,
    QTabWidget, QTabBar, QProgressBar, QStackedWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QProcess, QProcessEnvironment, QObject, QRegularExpression, QTimer
from PyQt6.QtGui import QFont, QIcon, QAction, QTextCursor, QSyntaxHighlighter, QTextCharFormat, QColor

from services.python_service import PythonService
from services.dependency_service import DependencyService
from ui.theme import set_button_variant


class PythonSyntaxHighlighter(QSyntaxHighlighter):
    """Python syntax highlighter for code editor."""

    def __init__(self, document):
        super().__init__(document)
        self._rules = []

        # Keywords — blue bold
        kw_fmt = QTextCharFormat()
        kw_fmt.setForeground(QColor("#0000FF"))
        kw_fmt.setFontWeight(QFont.Weight.Bold)
        keywords = [
            "and", "as", "assert", "async", "await", "break", "class", "continue",
            "def", "del", "elif", "else", "except", "finally", "for", "from",
            "global", "if", "import", "in", "is", "lambda", "nonlocal", "not",
            "or", "pass", "raise", "return", "try", "while", "with", "yield",
            "True", "False", "None",
        ]
        for word in keywords:
            self._rules.append((QRegularExpression(r"\b" + word + r"\b"), kw_fmt))

        # Built-in functions — deep blue
        builtin_fmt = QTextCharFormat()
        builtin_fmt.setForeground(QColor("#0078D4"))
        builtins = [
            "abs", "all", "any", "bin", "bool", "bytes", "chr", "dict", "dir",
            "enumerate", "eval", "exec", "filter", "float", "format", "frozenset",
            "getattr", "hasattr", "hash", "hex", "id", "input", "int", "isinstance",
            "issubclass", "iter", "len", "list", "map", "max", "min", "next",
            "object", "oct", "open", "ord", "pow", "print", "property", "range",
            "repr", "reversed", "round", "set", "setattr", "slice", "sorted",
            "str", "sum", "super", "tuple", "type", "vars", "zip",
            "Exception", "ValueError", "TypeError", "KeyError", "IndexError",
            "FileNotFoundError", "OSError", "RuntimeError", "StopIteration",
            "self", "cls",
        ]
        for word in builtins:
            self._rules.append((QRegularExpression(r"\b" + word + r"\b"), builtin_fmt))

        # Decorators — dark green
        deco_fmt = QTextCharFormat()
        deco_fmt.setForeground(QColor("#006600"))
        deco_fmt.setFontWeight(QFont.Weight.Bold)
        self._rules.append((QRegularExpression(r"@\w+"), deco_fmt))

        # Strings — green
        str_fmt = QTextCharFormat()
        str_fmt.setForeground(QColor("#008000"))
        self._rules.append((QRegularExpression(r"'[^']*'"), str_fmt))
        self._rules.append((QRegularExpression(r'"[^"]*"'), str_fmt))
        self._rules.append((QRegularExpression(r"'''[^']*'''"), str_fmt))
        self._rules.append((QRegularExpression(r'"""[^"]*"""'), str_fmt))

        # f-strings — lighter green
        fstr_fmt = QTextCharFormat()
        fstr_fmt.setForeground(QColor("#00A000"))
        self._rules.append((QRegularExpression(r"""f'[^']*'"""), fstr_fmt))
        self._rules.append((QRegularExpression(r'f"[^"]*"'), fstr_fmt))

        # Numbers — orange
        num_fmt = QTextCharFormat()
        num_fmt.setForeground(QColor("#FF6600"))
        self._rules.append((QRegularExpression(r"\b[0-9]+\.?[0-9]*[eE]?[+-]?[0-9]*\b"), num_fmt))
        self._rules.append((QRegularExpression(r"\b0[xX][0-9a-fA-F]+\b"), num_fmt))

        # Comments — gray italic
        cmt_fmt = QTextCharFormat()
        cmt_fmt.setForeground(QColor("#808080"))
        cmt_fmt.setFontItalic(True)
        self._rules.append((QRegularExpression(r"#[^\n]*"), cmt_fmt))

    def highlightBlock(self, text):
        for pattern, fmt in self._rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                match = it.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)


class ScriptDialog(QDialog):
    """Dialog for creating or editing a script."""

    def __init__(self, parent=None, script_data=None, scripts_dir=None):
        """Initialize the script dialog.

        Args:
            parent: Parent widget
            script_data: Existing script data for edit mode, None for create mode
            scripts_dir: Scripts directory for file selection
        """
        super().__init__(parent)
        self.script_data = script_data
        self.is_edit_mode = script_data is not None
        self.scripts_dir = scripts_dir
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("编辑脚本" if self.is_edit_mode else "新增脚本")
        self.setMinimumSize(700, 550)
        self.setModal(True)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Name field
        name_layout = QHBoxLayout()
        name_label = QLabel("脚本名称:")
        name_label.setFixedWidth(80)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("请输入脚本名称")
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        main_layout.addLayout(name_layout)

        # Description field (multi-line)
        desc_label = QLabel("功能描述:")
        desc_label.setFixedWidth(80)
        self.desc_editor = QTextEdit()
        self.desc_editor.setPlaceholderText("请输入脚本功能描述（可选，支持多行）")
        self.desc_editor.setMaximumHeight(80)
        self.desc_editor.setFont(QFont("Microsoft YaHei", 9))

        desc_wrapper = QHBoxLayout()
        desc_wrapper.addWidget(desc_label)
        desc_wrapper.addWidget(self.desc_editor)
        main_layout.addLayout(desc_wrapper)

        # File path field (only for create mode)
        if not self.is_edit_mode and self.scripts_dir:
            file_layout = QHBoxLayout()
            file_label = QLabel("保存路径:")
            file_label.setFixedWidth(80)
            self.file_input = QLineEdit()
            self.file_input.setPlaceholderText(f"默认：{self.scripts_dir}")
            browse_btn = QPushButton("浏览...")
            browse_btn.setFixedWidth(80)
            browse_btn.clicked.connect(self._browse_file)
            file_layout.addWidget(file_label)
            file_layout.addWidget(self.file_input)
            file_layout.addWidget(browse_btn)
            main_layout.addLayout(file_layout)

        # Code editor label
        code_label = QLabel("代码:")
        main_layout.addWidget(code_label)

        self.code_editor = QTextEdit()
        self.code_editor.setFont(QFont("Consolas", 10))
        self.code_editor.setPlaceholderText("请输入 Python 代码...")
        self._highlighter = PythonSyntaxHighlighter(self.code_editor.document())
        main_layout.addWidget(self.code_editor)

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
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #006cbd;
            }
        """)
        self.save_btn.clicked.connect(self._on_save)
        button_layout.addWidget(self.save_btn)

        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

    def _browse_file(self):
        """Open file dialog to select save path."""
        if self.scripts_dir:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "选择脚本保存路径",
                self.scripts_dir,
                "Python Files (*.py);;All Files (*)"
            )
            if file_path:
                self.file_input.setText(file_path)

    def _load_data(self):
        """Load existing script data for edit mode."""
        if self.is_edit_mode and self.script_data:
            self.name_input.setText(self.script_data.get("name", ""))
            self.desc_editor.setPlainText(self.script_data.get("description", ""))
            self.code_editor.setPlainText(self.script_data.get("code", ""))

    def _on_save(self):
        """Handle save button click."""
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "警告", "请输入脚本名称")
            return

        # Validate name: reject characters unsafe for filenames
        invalid_chars = set(r'<>:"/\|?*')
        found = invalid_chars & set(name)
        if found:
            QMessageBox.warning(
                self, "无效的脚本名称",
                f"脚本名称不能包含以下字符：\n  {' '.join(sorted(found))}\n\n"
                f"请修改后再保存。"
            )
            return

        code = self.code_editor.toPlainText()
        if not code:
            QMessageBox.warning(self, "警告", "请输入脚本代码")
            return

        self.accept()

    def get_script_data(self):
        """Get the script data from the dialog.

        Returns:
            Dictionary with name, description, code, and optional file_path
        """
        data = {
            "name": self.name_input.text().strip(),
            "description": self.desc_editor.toPlainText().strip(),
            "code": self.code_editor.toPlainText()
        }
        if hasattr(self, 'file_input') and self.file_input.text().strip():
            data["file_path"] = self.file_input.text().strip()
        return data


class DropLineEdit(QLineEdit):
    """QLineEdit that accepts file drops and inserts the absolute path."""

    _BASE_STYLE = """
        QLineEdit {
            background-color: #2d2d2d;
            color: #d4d4d4;
            border: 1px solid #444;
            border-radius: 3px;
            padding: 5px;
        }
        QLineEdit:disabled {
            background-color: #1e1e1e;
            color: #666;
        }
    """
    _DRAG_STYLE = """
        QLineEdit {
            background-color: #2d2d2d;
            color: #d4d4d4;
            border: 2px solid #4caf50;
            border-radius: 3px;
            padding: 5px;
        }
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setStyleSheet(self._BASE_STYLE)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            self.setStyleSheet(self._DRAG_STYLE)
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.setStyleSheet(self._BASE_STYLE)
        super().dragLeaveEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        self.setStyleSheet(self._BASE_STYLE)
        urls = event.mimeData().urls()
        if urls:
            paths = []
            for url in urls:
                path = url.toLocalFile()
                if path:
                    paths.append(path)
            if paths:
                current = self.text()
                new_text = " ".join(paths)
                if current:
                    self.setText(current + " " + new_text)
                else:
                    self.setText(new_text)
            event.acceptProposedAction()


class _DropOutputTextEdit(QTextEdit):
    """QTextEdit that accepts file drops and appends the absolute paths."""

    _DRAG_STYLE = """
        QTextEdit {
            background-color: #1e1e1e;
            color: #d4d4d4;
            border: 2px solid #4caf50;
            border-radius: 3px;
            padding: 5px;
        }
    """
    _BASE_STYLE = """
        QTextEdit {
            background-color: #1e1e1e;
            color: #d4d4d4;
            border: 1px solid #333;
            border-radius: 3px;
            padding: 5px;
        }
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._base_overridden = False

    def setBaseStyleSheet(self, style: str):
        """Set an external base stylesheet to restore after drag."""
        self._BASE_STYLE = style
        self._base_overridden = True

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            self.setStyleSheet(self._DRAG_STYLE)
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.setStyleSheet(self._BASE_STYLE)
        super().dragLeaveEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        self.setStyleSheet(self._BASE_STYLE)
        urls = event.mimeData().urls()
        if urls:
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.setTextCursor(cursor)
            for url in urls:
                path = url.toLocalFile()
                if path:
                    self.insertPlainText(path + "\n")
            self.ensureCursorVisible()
            event.acceptProposedAction()


class InteractiveOutputWidget(QWidget):
    """Interactive output widget with status bar, progress bar, display area and input line."""

    input_sent = pyqtSignal(str)  # User input submitted

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_running = False
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # ── Status Header ──
        status_header = QWidget()
        sh_layout = QHBoxLayout()
        sh_layout.setContentsMargins(6, 2, 8, 2)
        sh_layout.setSpacing(5)

        self.status_dot = QLabel("●")
        self.status_dot.setFixedWidth(14)
        self.status_dot.setStyleSheet(
            "color: #aaa; font-size: 11px; font-weight: bold;")

        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #aaa; font-size: 11px;")

        self.elapsed_label = QLabel("")
        self.elapsed_label.setStyleSheet("color: #777; font-size: 10px;")

        sh_layout.addWidget(self.status_dot)
        sh_layout.addWidget(self.status_label)
        sh_layout.addStretch()
        sh_layout.addWidget(self.elapsed_label)

        status_header.setLayout(sh_layout)
        status_header.setFixedHeight(22)
        layout.addWidget(status_header)

        # ── Progress Bar (indeterminate, only shown while running) ──
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setMaximumHeight(3)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #2d2d2d;
            }
            QProgressBar::chunk {
                background-color: #4caf50;
            }
        """)
        layout.addWidget(self.progress_bar)

        # ── Output display (read-only, supports file drop to show path) ──
        self.output_display = _DropOutputTextEdit()
        self.output_display.setReadOnly(True)
        self.output_display.setFont(QFont("Consolas", 10))
        _output_style = """
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #333;
                border-radius: 3px;
                padding: 5px;
            }
        """
        self.output_display.setStyleSheet(_output_style)
        self.output_display.setBaseStyleSheet(_output_style)
        self.output_display.setPlaceholderText("运行结果将显示在这里...\n也可拖拽文件到此区域，显示绝对路径")
        self.output_display.setMinimumHeight(80)
        layout.addWidget(self.output_display)

        # ── Input row: input line + send button ──
        input_row = QWidget()
        ir_layout = QHBoxLayout()
        ir_layout.setContentsMargins(0, 0, 0, 0)
        ir_layout.setSpacing(4)

        self.input_line = DropLineEdit()
        self.input_line.setFont(QFont("Consolas", 10))
        self.input_line.setPlaceholderText("输入内容或拖拽文件到此处，按 Enter 发送...")
        self.input_line.setEnabled(False)
        self.input_line.returnPressed.connect(self._on_input_submit)
        ir_layout.addWidget(self.input_line)

        self.send_btn = QPushButton("发送")
        self.send_btn.setFixedSize(56, 28)
        self.send_btn.setEnabled(False)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078D4;
                color: white;
                border: none;
                border-radius: 3px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #006cbd;
            }
            QPushButton:disabled {
                background-color: #444;
                color: #888;
            }
        """)
        self.send_btn.clicked.connect(self._on_input_submit)
        ir_layout.addWidget(self.send_btn)

        input_row.setLayout(ir_layout)
        layout.addWidget(input_row)

        self.setLayout(layout)

    # ── Status display methods ──

    def set_status(self, status_text: str, dot_color: str = "#aaa"):
        """Update the status indicator text and dot color.

        Args:
            status_text: Status description (e.g. '运行中', '已完成', '失败')
            dot_color: CSS color for the status dot
        """
        self.status_label.setText(status_text)
        self.status_dot.setStyleSheet(
            f"color: {dot_color}; font-size: 11px; font-weight: bold;")

    def update_elapsed(self, total_seconds: int):
        """Update elapsed time display.

        Args:
            total_seconds: Total elapsed seconds, or -1 to clear
        """
        if total_seconds < 0:
            self.elapsed_label.setText("")
            return
        h = total_seconds // 3600
        m = (total_seconds % 3600) // 60
        s = total_seconds % 60
        if h > 0:
            self.elapsed_label.setText(f"耗时: {h}:{m:02d}:{s:02d}")
        else:
            self.elapsed_label.setText(f"耗时: {m:02d}:{s:02d}")

    # ── Output / input methods ──

    def append_output(self, text: str, is_error: bool = False):
        cursor = self.output_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.output_display.setTextCursor(cursor)

        if is_error:
            self.output_display.insertHtml(f'<span style="color: #f44;">{text}</span>')
        else:
            self.output_display.insertPlainText(text)

        self.output_display.ensureCursorVisible()

    def set_running_mode(self, is_running: bool):
        self._is_running = is_running
        self.input_line.setEnabled(is_running)
        self.send_btn.setEnabled(is_running)
        self.progress_bar.setVisible(is_running)
        if is_running:
            self.input_line.setFocus()
        else:
            self.input_line.clear()

    def clear_output(self):
        self.output_display.clear()

    def _on_input_submit(self):
        if not self._is_running:
            return
        text = self.input_line.text()
        if text:
            self.input_sent.emit(text)
            self.input_line.clear()
            self.append_output(f"> {text}\n")


class OutputTabWidget(QWidget):
    """Tabbed container for multiple InteractiveOutputWidget instances.

    Each running script gets its own tab with status bar, elapsed time,
    and progress indicator. Tabs can be closed to stop the process.
    """

    tab_close_requested = pyqtSignal(str)  # run_id
    tab_focus_changed = pyqtSignal(str)    # run_id (empty string if no tabs)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tabs: dict[str, InteractiveOutputWidget] = {}
        self._run_name_counts: dict[str, int] = {}
        self._run_start_times: dict[str, float] = {}

        self._elapsed_timer = QTimer(self)
        self._elapsed_timer.setInterval(1000)
        self._elapsed_timer.timeout.connect(self._on_elapsed_tick)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # QStackedWidget: page 0 = tab_widget, page 1 = placeholder
        self._stack = QStackedWidget()

        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self._on_tab_close)
        self.tab_widget.currentChanged.connect(self._on_current_changed)
        self.tab_widget.setDocumentMode(True)
        self._stack.addWidget(self.tab_widget)  # index 0

        self._placeholder = QLabel("点击「运行」执行脚本，输出将显示在此处")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setStyleSheet("""
            QLabel {
                color: #999;
                font-size: 13px;
                padding: 30px;
                background-color: #1e1e1e;
                border: 1px solid #333;
                border-radius: 3px;
            }
        """)
        self._placeholder.setMinimumHeight(80)
        self._stack.addWidget(self._placeholder)  # index 1

        self._stack.setCurrentIndex(1)  # show placeholder initially
        layout.addWidget(self._stack)

        self.setLayout(layout)

    def add_run_tab(self, run_id: str, script_name: str,
                    process_manager: "ScriptProcessManager") -> InteractiveOutputWidget:
        count = self._run_name_counts.get(script_name, 0) + 1
        self._run_name_counts[script_name] = count
        tab_title = f"{script_name} ({count})" if count > 1 else script_name

        output_widget = InteractiveOutputWidget()
        output_widget.input_sent.connect(
            lambda text, rid=run_id: process_manager.send_input(rid, text))

        self.tab_widget.addTab(output_widget, tab_title)
        self._tabs[run_id] = output_widget

        self._update_visibility()
        self.tab_widget.setCurrentWidget(output_widget)

        # Enable input immediately — process is already starting.
        # This avoids a race where the QProcess.started signal fires
        # before the tab is registered in self._tabs.
        output_widget.set_running_mode(True)
        return output_widget

    # ── Elapsed time tracking ──

    def start_tracking(self, run_id: str):
        """Start elapsed time tracking for a run."""
        import time
        self._run_start_times[run_id] = time.time()
        tab = self._tabs.get(run_id)
        if tab:
            tab.set_status("运行中", "#4caf50")
            tab.update_elapsed(0)
        if not self._elapsed_timer.isActive():
            self._elapsed_timer.start()

    def stop_tracking(self, run_id: str, exit_code: int = 0, killed: bool = False):
        """Stop elapsed time tracking and show final status."""
        self._run_start_times.pop(run_id, None)
        if not self._run_start_times:
            self._elapsed_timer.stop()

        tab = self._tabs.get(run_id)
        if tab:
            if killed:
                tab.set_status("已停止", "#f90")
            elif exit_code == 0:
                tab.set_status("已完成", "#4caf50")
            else:
                tab.set_status(f"失败 (退出码: {exit_code})", "#f44")

    def _on_elapsed_tick(self):
        """Update elapsed time for all tracked runs (called every second)."""
        import time
        now = time.time()
        for run_id, start_time in list(self._run_start_times.items()):
            tab = self._tabs.get(run_id)
            if tab:
                tab.update_elapsed(int(now - start_time))

    # ── Output routing ──

    def append_output(self, run_id: str, text: str, is_error: bool = False):
        output_widget = self._tabs.get(run_id)
        if output_widget:
            output_widget.append_output(text, is_error)

    def set_tab_running(self, run_id: str, is_running: bool):
        output_widget = self._tabs.get(run_id)
        if output_widget:
            output_widget.set_running_mode(is_running)

    def mark_tab_finished(self, run_id: str, exit_code: int):
        for i in range(self.tab_widget.count()):
            if self.tab_widget.widget(i) is self._tabs.get(run_id):
                title = self.tab_widget.tabText(i)
                if exit_code == 0:
                    self.tab_widget.setTabText(i, f"{title} ✓")
                else:
                    self.tab_widget.setTabText(i, f"{title} ✗({exit_code})")
                break

    def remove_tab(self, run_id: str):
        self._run_start_times.pop(run_id, None)
        if not self._run_start_times:
            self._elapsed_timer.stop()
        output_widget = self._tabs.pop(run_id, None)
        if output_widget:
            idx = self.tab_widget.indexOf(output_widget)
            if idx >= 0:
                self.tab_widget.removeTab(idx)
        self._update_visibility()

    def get_active_run_id(self) -> str:
        current = self.tab_widget.currentWidget()
        for rid, w in self._tabs.items():
            if w is current:
                return rid
        return ""

    def has_runs(self) -> bool:
        return len(self._tabs) > 0

    # ── Internal handlers ──

    def _on_tab_close(self, index: int):
        widget = self.tab_widget.widget(index)
        for rid, w in self._tabs.items():
            if w is widget:
                self.tab_close_requested.emit(rid)
                return

    def _on_current_changed(self, index: int):
        if index >= 0:
            widget = self.tab_widget.widget(index)
            for rid, w in self._tabs.items():
                if w is widget:
                    self.tab_focus_changed.emit(rid)
                    return
        self.tab_focus_changed.emit("")

    def _update_visibility(self):
        self._stack.setCurrentIndex(0 if self._tabs else 1)


class ScriptProcessManager(QObject):
    """Manages multiple QProcess instances for concurrent script execution.

    Each run is identified by a unique run_id. Signals include the run_id
    as the first argument so the UI can route output to the correct tab.
    """

    # Signals — first arg is always run_id
    output_received = pyqtSignal(str, str)       # run_id, stdout text
    error_received = pyqtSignal(str, str)        # run_id, stderr text
    process_started = pyqtSignal(str)             # run_id
    process_finished = pyqtSignal(str, int, int)  # run_id, exitCode, exitStatus
    input_required = pyqtSignal(str)             # run_id
    all_finished = pyqtSignal()                  # emitted when last run finishes

    def __init__(self, parent=None):
        super().__init__(parent)
        self._runs: dict[str, dict] = {}
        self._run_counter = 0

    def reserve_run_id(self) -> str:
        """Allocate a run_id without starting a process yet."""
        self._run_counter += 1
        return f"run-{self._run_counter}"

    def start_script_with_id(self, run_id: str, script_path: str,
                             working_dir: str, script_dir: str = "",
                             is_temp: bool = False, script_name: str = ""):
        """Start a script execution with a pre-reserved run_id.

        The caller must have already created the output tab via
        OutputTabWidget.add_run_tab() so the input line is ready.
        """
        process = QProcess(self)
        process.setWorkingDirectory(working_dir)

        env = QProcessEnvironment.systemEnvironment()
        env.insert("PYTHONIOENCODING", "utf-8")
        env.insert("PYTHONUNBUFFERED", "1")
        if script_dir:
            existing = env.value("PYTHONPATH", "")
            if existing:
                env.insert("PYTHONPATH", script_dir + os.pathsep + existing)
            else:
                env.insert("PYTHONPATH", script_dir)
        process.setProcessEnvironment(env)

        self._runs[run_id] = {
            "process": process,
            "script_name": script_name,
            "temp_file_path": script_path if is_temp else None,
            "_is_temp": is_temp,
            "_stdout_buf": b"",
            "_stderr_buf": b"",
        }

        process.readyReadStandardOutput.connect(
            lambda rid=run_id: self._on_stdout_ready(rid))
        process.readyReadStandardError.connect(
            lambda rid=run_id: self._on_stderr_ready(rid))
        process.started.connect(
            lambda rid=run_id: self._on_process_started(rid))
        process.finished.connect(
            lambda ec, es, rid=run_id: self._on_process_finished(rid, ec, es))
        process.errorOccurred.connect(
            lambda err, rid=run_id: self._on_process_error(rid, err))

        process.start("python", ["-u", script_path])

    def start_script(self, script_path: str, working_dir: str,
                     script_dir: str = "", is_temp: bool = False,
                     script_name: str = "") -> str:
        """Start a new script execution. Returns a unique run_id.

        Prefer using reserve_run_id() + start_script_with_id() in new code
        so the output tab can be created before the process starts.
        """
        run_id = self.reserve_run_id()
        self.start_script_with_id(run_id, script_path, working_dir,
                                  script_dir, is_temp, script_name)
        return run_id

    def send_input(self, run_id: str, text: str):
        """Send user input to a specific running process.

        Args:
            run_id: The run identifier
            text: User input text
        """
        run = self._runs.get(run_id)
        if run:
            process = run["process"]
            if process.state() == QProcess.ProcessState.Running:
                data = (text + "\n").encode('utf-8')
                process.write(data)

    def stop(self, run_id: str):
        """Stop a specific running process.

        Args:
            run_id: The run identifier
        """
        run = self._runs.get(run_id)
        if run:
            process = run["process"]
            if process.state() == QProcess.ProcessState.Running:
                process.kill()
            self._cleanup_temp_file(run_id)

    def stop_all(self):
        """Stop all running processes."""
        for run_id in list(self._runs.keys()):
            self.stop(run_id)

    def is_running(self, run_id: str = None) -> bool:
        """Check if a process (or any process) is running.

        Args:
            run_id: Specific run ID, or None to check all runs

        Returns:
            True if running, False otherwise
        """
        if run_id:
            run = self._runs.get(run_id)
            return bool(run and run["process"].state() == QProcess.ProcessState.Running)
        return any(
            r["process"].state() == QProcess.ProcessState.Running
            for r in self._runs.values()
        )

    def get_run_info(self, run_id: str) -> dict | None:
        """Get info about a specific run."""
        return self._runs.get(run_id)

    def active_run_count(self) -> int:
        """Return the number of currently running processes."""
        return sum(
            1 for r in self._runs.values()
            if r["process"].state() == QProcess.ProcessState.Running
        )

    def _decode_chunk(self, run_id: str, data: bytes, is_stderr: bool = False) -> str:
        """Decode a byte chunk handling multi-byte UTF-8 splits across reads."""
        run = self._runs.get(run_id)
        if not run:
            return ""
        buf_attr = '_stderr_buf' if is_stderr else '_stdout_buf'
        prev = run.get(buf_attr, b'')
        combined = prev + bytes(data)
        try:
            text = combined.decode('utf-8')
            run[buf_attr] = b''
            return text
        except UnicodeDecodeError as e:
            valid = combined[:e.start].decode('utf-8')
            run[buf_attr] = combined[e.start:]
            return valid

    def _flush_buffer(self, run_id: str, is_stderr: bool = False):
        """Flush any remaining bytes in the buffer (called on process finish)."""
        run = self._runs.get(run_id)
        if not run:
            return ""
        buf_attr = '_stderr_buf' if is_stderr else '_stdout_buf'
        buf = run.get(buf_attr, b'')
        if buf:
            run[buf_attr] = b''
            return buf.decode('utf-8', errors='replace')
        return ""

    def _on_stdout_ready(self, run_id: str):
        """Handle stdout data available for a specific run."""
        run = self._runs.get(run_id)
        if not run:
            return
        data = run["process"].readAllStandardOutput()
        text = self._decode_chunk(run_id, data, is_stderr=False)
        if text:
            self.output_received.emit(run_id, text)
            if self._detect_input_prompt(text):
                self.input_required.emit(run_id)

    def _on_stderr_ready(self, run_id: str):
        """Handle stderr data available for a specific run."""
        run = self._runs.get(run_id)
        if not run:
            return
        data = run["process"].readAllStandardError()
        text = self._decode_chunk(run_id, data, is_stderr=True)
        if text:
            self.error_received.emit(run_id, text)

    def _on_process_started(self, run_id: str):
        """Handle process started."""
        self.process_started.emit(run_id)

    def _on_process_finished(self, run_id: str, exit_code: int, exit_status: int):
        """Handle process finished.

        Args:
            run_id: The run identifier
            exit_code: Process exit code
            exit_status: QProcess.ExitStatus value
        """
        for buf_type in (False, True):
            tail = self._flush_buffer(run_id, is_stderr=buf_type)
            if tail:
                (self.error_received if buf_type else self.output_received).emit(run_id, tail)

        self._cleanup_temp_file(run_id)
        self.process_finished.emit(run_id, exit_code, exit_status)

        # Clean up finished run from tracking after a short delay
        # (so is_running still reports correctly in process_finished handler)
        QTimer.singleShot(100, lambda rid=run_id: self._prune_run(rid))

        if self.active_run_count() == 0:
            self.all_finished.emit()

    def _on_process_error(self, run_id: str, error: QProcess.ProcessError):
        """Handle process error — emit error message; for FailedToStart, also finalize."""
        error_names = {
            QProcess.ProcessError.FailedToStart: "启动失败",
            QProcess.ProcessError.Crashed: "进程崩溃",
            QProcess.ProcessError.Timedout: "超时",
            QProcess.ProcessError.WriteError: "写入错误",
            QProcess.ProcessError.ReadError: "读取错误",
            QProcess.ProcessError.UnknownError: "未知错误"
        }
        error_msg = error_names.get(error, "未知错误")
        self.error_received.emit(run_id, f"\n进程错误: {error_msg}\n")
        # FailedToStart never triggers finished(), so finalize manually
        if error == QProcess.ProcessError.FailedToStart:
            self.process_finished.emit(run_id, -1, 1)

    def _detect_input_prompt(self, text: str) -> bool:
        """Detect if text indicates input prompt from Python input()."""
        if not text:
            return False
        text = text.rstrip()
        if not text:
            return False
        return text.endswith(':') or text.endswith('?') or text.endswith('：')

    def _cleanup_temp_file(self, run_id: str):
        """Clean up temporary script file for a specific run."""
        run = self._runs.get(run_id)
        if not run:
            return
        temp_path = run.get("temp_file_path")
        is_temp = run.get("_is_temp", False)
        if temp_path and is_temp:
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            except Exception:
                pass
            run["temp_file_path"] = None

    def _prune_run(self, run_id: str):
        """Remove a finished run from tracking after cleanup."""
        run = self._runs.get(run_id)
        if run and run["process"].state() == QProcess.ProcessState.NotRunning:
            run["process"].deleteLater()
            del self._runs[run_id]


class PythonModule(QWidget):
    """Python script management module with tree view and code editor.

    Features:
        - QTreeWidget for tree-structured script list
        - Code editor for viewing/editing scripts
        - Buttons: Add, Edit, Delete, Run, Check Dependencies
        - ScriptDialog for creating/editing scripts
        - Async script execution with QThread
    """

    # Signals
    script_added = pyqtSignal()
    script_deleted = pyqtSignal()
    script_updated = pyqtSignal()

    def __init__(self, db_path: str, whl_dir: str, parent=None):
        """Initialize the Python module.

        Args:
            db_path: Path to the SQLite database
            whl_dir: Path to the whl file pool directory
            parent: Parent widget
        """
        super().__init__(parent)
        self.db_path = db_path
        self.whl_dir = whl_dir

        # Initialize services
        self.python_service = PythonService(db_path)
        self.dependency_service = DependencyService(whl_dir)
        self.dependency_service.set_python_service(self.python_service)

        # Cache for installed packages
        self._installed_packages_cache = None
        self._packages_cache_time = 0

        # Track dialog state to prevent duplicates
        self._dialog_open = False

        # Script process manager for concurrent script execution
        self.process_manager = ScriptProcessManager(self)
        self.process_manager.output_received.connect(self._on_output_received)
        self.process_manager.error_received.connect(self._on_error_received)
        self.process_manager.process_started.connect(self._on_process_started)
        self.process_manager.process_finished.connect(self._on_process_finished)
        self.process_manager.input_required.connect(self._on_input_required)

        self._setup_ui()

        # Connect tab close requests to stop the corresponding process
        self.output_tabs.tab_close_requested.connect(self._on_tab_close_requested)

        self._refresh_tree()

    def _setup_ui(self):
        """Set up the module UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(26, 22, 26, 22)
        layout.setSpacing(12)

        # Title (compact with toolbar)
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(10)

        title_label = QLabel("Python 脚本管理")
        title_label.setStyleSheet("font-size: 21px; font-weight: 700; color: #202333;")
        title_label.setFixedHeight(38)
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        layout.addLayout(title_layout)

        # Toolbar
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(8)
        toolbar_layout.setContentsMargins(0, 0, 0, 5)

        self.add_btn = QPushButton("+ 新增")
        self.add_btn.setFixedHeight(35)
        set_button_variant(self.add_btn, "primary")
        self.add_btn.clicked.connect(self._on_add_script)
        toolbar_layout.addWidget(self.add_btn)

        self.edit_btn = QPushButton("修改")
        self.edit_btn.setFixedHeight(35)
        self.edit_btn.clicked.connect(self._on_edit_script)
        toolbar_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("删除")
        self.delete_btn.setFixedHeight(35)
        set_button_variant(self.delete_btn, "danger")
        self.delete_btn.clicked.connect(self._on_delete_script)
        toolbar_layout.addWidget(self.delete_btn)

        toolbar_layout.addSpacing(20)

        self.run_btn = QPushButton("运行")
        self.run_btn.setFixedHeight(35)
        set_button_variant(self.run_btn, "success")
        self.run_btn.clicked.connect(self._on_run_script)
        toolbar_layout.addWidget(self.run_btn)

        self.check_deps_btn = QPushButton("检测依赖")
        self.check_deps_btn.setFixedHeight(35)
        self.check_deps_btn.clicked.connect(self._on_check_dependencies)
        toolbar_layout.addWidget(self.check_deps_btn)

        self.download_whl_btn = QPushButton("下载 WHL")
        self.download_whl_btn.setFixedHeight(35)
        self.download_whl_btn.clicked.connect(self._on_download_whl)
        toolbar_layout.addWidget(self.download_whl_btn)

        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.setFixedHeight(35)
        self.refresh_btn.clicked.connect(self._on_refresh)
        toolbar_layout.addWidget(self.refresh_btn)

        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)

        # Splitter for tree and editor
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel - Tree view
        tree_panel = QFrame()
        tree_layout = QVBoxLayout()
        tree_layout.setContentsMargins(0, 0, 0, 0)
        tree_layout.setSpacing(3)

        tree_label = QLabel("脚本列表")
        tree_label.setStyleSheet("font-weight: 600; color: #555A70; padding: 7px 4px;")
        tree_label.setFixedHeight(34)
        tree_layout.addWidget(tree_label)

        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["名称", "描述"])
        self.tree_widget.setColumnWidth(0, 150)
        self.tree_widget.setColumnWidth(1, 150)
        self.tree_widget.setExpandsOnDoubleClick(True)
        self.tree_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree_widget.customContextMenuRequested.connect(self._on_tree_context_menu)
        self.tree_widget.itemSelectionChanged.connect(self._on_tree_selection_changed)
        tree_layout.addWidget(self.tree_widget)

        tree_panel.setLayout(tree_layout)

        # Right panel - Code editor
        editor_panel = QFrame()
        editor_layout = QVBoxLayout()
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.setSpacing(3)

        editor_label = QLabel("代码编辑器")
        editor_label.setStyleSheet("font-weight: 600; color: #555A70; padding: 7px 4px;")
        editor_label.setFixedHeight(34)
        editor_layout.addWidget(editor_label)

        self.code_editor = QTextEdit()
        self.code_editor.setFont(QFont("Consolas", 10))
        self.code_editor.setStyleSheet("QTextEdit { background: #FFFFFF; border: 1px solid #E3E6EF; border-radius: 8px; padding: 10px; }")
        self.code_editor.setReadOnly(True)
        self.code_editor.setPlaceholderText("选择脚本查看代码...")
        self._highlighter = PythonSyntaxHighlighter(self.code_editor.document())
        editor_layout.addWidget(self.code_editor)

        # Script info panel (file path and timestamps)
        self.script_info_label = QLabel("")
        self.script_info_label.setStyleSheet("""
            QLabel {
                color: #7B7F91;
                font-size: 10px;
                padding: 7px 9px;
                background-color: #F8F9FC;
                border: 1px solid #E3E6EF;
                border-radius: 6px;
            }
        """)
        self.script_info_label.setWordWrap(True)
        editor_layout.addWidget(self.script_info_label)

        editor_panel.setLayout(editor_layout)

        splitter.addWidget(tree_panel)
        splitter.addWidget(editor_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        # Output panel — tabbed container for multiple concurrent script runs
        output_panel = QWidget()
        op_layout = QVBoxLayout()
        op_layout.setContentsMargins(0, 0, 0, 0)
        op_layout.setSpacing(0)

        output_label = QLabel("输出 — 每个脚本运行在独立的标签页中")
        output_label.setStyleSheet("font-weight: 600; color: #555A70; padding: 7px 4px;")
        output_label.setFixedHeight(34)
        op_layout.addWidget(output_label)

        self.output_tabs = OutputTabWidget()
        op_layout.addWidget(self.output_tabs)
        output_panel.setLayout(op_layout)

        # Wrap main content and output in a vertical splitter for resizable output area
        vsplit = QSplitter(Qt.Orientation.Vertical)
        vsplit.setHandleWidth(4)
        vsplit.addWidget(splitter)       # top: tree | editor
        vsplit.addWidget(output_panel)   # bottom: output area
        vsplit.setStretchFactor(0, 3)
        vsplit.setStretchFactor(1, 1)
        vsplit.setChildrenCollapsible(False)

        layout.addWidget(vsplit)

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

    def _refresh_tree(self):
        """Refresh the tree view with current scripts."""
        self.tree_widget.clear()

        tree_data = self.python_service.get_tree()
        self._add_tree_items(tree_data, None)

    def _add_tree_items(self, items, parent_item):
        """Add tree items recursively.

        Args:
            items: List of script data dictionaries
            parent_item: Parent QTreeWidgetItem or None for root items
        """
        for item in items:
            tree_item = QTreeWidgetItem()
            tree_item.setData(0, Qt.ItemDataRole.UserRole, item["id"])
            tree_item.setText(0, item["name"])
            tree_item.setText(1, item.get("description", "")[:50])

            if parent_item is None:
                self.tree_widget.addTopLevelItem(tree_item)
            else:
                parent_item.addChild(tree_item)

            if item.get("children"):
                self._add_tree_items(item["children"], tree_item)

    def _on_tree_selection_changed(self):
        """Handle tree selection change."""
        selected_items = self.tree_widget.selectedItems()
        if not selected_items:
            self.code_editor.clear()
            self.script_info_label.clear()
            return

        item = selected_items[0]
        script_id = item.data(0, Qt.ItemDataRole.UserRole)

        if script_id:
            script = self.python_service.get_script(script_id)
            if script:
                self.code_editor.setPlainText(script.get("code", ""))
                # Update script info panel
                self._update_script_info(script)

    def _update_script_info(self, script):
        """Update the script info panel with file path and timestamps.

        Args:
            script: Script data dictionary
        """
        file_path = script.get("file_path", "")
        created_at = script.get("created_at", "")
        updated_at = script.get("updated_at", "")

        info_lines = []
        if file_path:
            info_lines.append(f"文件路径：{file_path}")
        if created_at:
            info_lines.append(f"创建时间：{created_at}")
        if updated_at:
            info_lines.append(f"修改时间：{updated_at}")

        if info_lines:
            self.script_info_label.setText(" | ".join(info_lines))
        else:
            self.script_info_label.clear()

    def _on_tree_context_menu(self, pos):
        """Handle tree widget context menu request.

        Args:
            pos: Position of the context menu request
        """
        item = self.tree_widget.itemAt(pos)
        if not item:
            return

        script_id = item.data(0, Qt.ItemDataRole.UserRole)
        if not script_id:
            return

        script = self.python_service.get_script(script_id)
        if not script:
            return

        # Create context menu
        menu = QMenu(self)

        # Properties action
        props_action = QAction("属性", self)
        props_action.triggered.connect(lambda: self._show_script_properties(script))
        menu.addAction(props_action)

        # Show menu
        menu.exec(self.tree_widget.viewport().mapToGlobal(pos))

    def _show_script_properties(self, script):
        """Show script properties dialog.

        Args:
            script: Script data dictionary
        """
        dialog = ScriptPropertiesDialog(self, script)
        dialog.exec()

    def _on_add_script(self):
        """Handle add script button click."""
        # Prevent duplicate dialogs
        if self._dialog_open:
            return

        # All new scripts are root-level (no parent-child relationships)
        parent_id = None

        self._dialog_open = True
        dialog = ScriptDialog(self, scripts_dir=self.python_service.scripts_dir)
        dialog.finished.connect(lambda: setattr(self, '_dialog_open', False))

        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_script_data()
            self.python_service.add_script(
                name=data["name"],
                code=data["code"],
                description=data["description"],
                parent_id=parent_id,
                file_path=data.get("file_path", "")
            )
            self._refresh_tree()
            self.script_added.emit()
            QMessageBox.information(self, "成功", "脚本已添加并保存到文件")

    def _on_edit_script(self):
        """Handle edit script button click."""
        # Prevent duplicate dialogs
        if self._dialog_open:
            return

        selected_items = self.tree_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请选择要修改的脚本")
            return

        item = selected_items[0]
        script_id = item.data(0, Qt.ItemDataRole.UserRole)

        if not script_id:
            QMessageBox.warning(self, "警告", "请选择有效的脚本")
            return

        script = self.python_service.get_script(script_id)
        if not script:
            QMessageBox.warning(self, "警告", "脚本不存在")
            return

        self._dialog_open = True
        # Pass scripts_dir for edit mode as well
        dialog = ScriptDialog(self, script_data=script, scripts_dir=self.python_service.scripts_dir)
        dialog.finished.connect(lambda: setattr(self, '_dialog_open', False))

        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_script_data()
            self.python_service.update_script(
                script_id=script_id,
                code=data["code"],
                name=data["name"],
                description=data["description"]
            )
            self._refresh_tree()
            self.script_updated.emit()
            QMessageBox.information(self, "成功", "脚本已更新并保存到文件")

    def _on_delete_script(self):
        """Handle delete script button click."""
        selected_items = self.tree_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请选择要删除的脚本")
            return

        item = selected_items[0]
        script_id = item.data(0, Qt.ItemDataRole.UserRole)

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
            if self.python_service.delete_script(script_id):
                self._refresh_tree()
                self.code_editor.clear()
                self.script_deleted.emit()
                QMessageBox.information(self, "成功", "脚本已从数据库和文件系统中删除")

    def _on_run_script(self):
        """Handle run script button click — starts a new concurrent script execution."""
        selected_items = self.tree_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请选择要运行的脚本")
            return

        item = selected_items[0]
        script_id = item.data(0, Qt.ItemDataRole.UserRole)

        if not script_id:
            QMessageBox.warning(self, "警告", "请选择有效的脚本")
            return

        # Get script name for display
        script = self.python_service.get_script(script_id)
        if not script:
            QMessageBox.warning(self, "警告", "脚本不存在")
            return

        script_name = script.get("name", f"脚本{script_id}")

        # Prepare script file for execution
        exec_info = self.python_service.prepare_script_for_execution(script_id)
        if not exec_info:
            QMessageBox.warning(self, "警告", "脚本不存在")
            return

        script_path = exec_info["path"]
        is_temp = exec_info["is_temp"]
        script_dir = exec_info["script_dir"]
        working_dir = self.python_service.get_working_directory()

        # Reserve run_id and create output tab BEFORE starting the process.
        # This guarantees the tab (with enabled input line) exists before
        # QProcess signals fire.
        run_id = self.process_manager.reserve_run_id()
        output_widget = self.output_tabs.add_run_tab(
            run_id, script_name, self.process_manager)
        output_widget.clear_output()
        output_widget.append_output(f"运行脚本「{script_name}」...\n")

        self.process_manager.start_script_with_id(
            run_id, script_path, working_dir,
            script_dir=script_dir, is_temp=is_temp,
            script_name=script_name,
        )

    def _on_tab_close_requested(self, run_id: str):
        """Handle tab close button — stop the corresponding process."""
        self.output_tabs.append_output(run_id, "\n正在停止脚本...\n")
        self.output_tabs.stop_tracking(run_id, killed=True)
        self.process_manager.stop(run_id)
        self.output_tabs.remove_tab(run_id)

    def _on_output_received(self, run_id: str, text: str):
        """Handle stdout data — route to the correct tab."""
        self.output_tabs.append_output(run_id, text)

    def _on_error_received(self, run_id: str, text: str):
        """Handle stderr data — route to the correct tab."""
        self.output_tabs.append_output(run_id, text, is_error=True)

    def _on_process_started(self, run_id: str):
        """Handle process started — enable input line and start elapsed timer."""
        self.output_tabs.set_tab_running(run_id, True)
        self.output_tabs.start_tracking(run_id)

    def _on_process_finished(self, run_id: str, exit_code: int, exit_status: int):
        """Handle process finished — disable input, stop timer, mark tab.

        Args:
            run_id: The run identifier
            exit_code: Process exit code (0 for success)
            exit_status: QProcess.ExitStatus (0 for normal exit, 1 for crash)
        """
        self.output_tabs.set_tab_running(run_id, False)
        self.output_tabs.stop_tracking(run_id, exit_code)
        self.output_tabs.mark_tab_finished(run_id, exit_code)

        if exit_code == 0:
            self.output_tabs.append_output(run_id, "\n脚本运行完成 (退出码: 0)\n")
        else:
            self.output_tabs.append_output(
                run_id,
                f"\n脚本运行失败 (退出码: {exit_code})\n",
                is_error=True,
            )

    def _on_input_required(self, run_id: str):
        """Handle input prompt detected — ensure input line is enabled."""
        self.output_tabs.set_tab_running(run_id, True)

    def _get_active_output(self) -> InteractiveOutputWidget:
        """Get an output widget for non-run system messages.

        Returns the currently active tab's output widget, or creates a
        generic output tab if none exist.
        """
        if self.output_tabs.has_runs():
            for i in range(self.output_tabs.tab_widget.count()):
                w = self.output_tabs.tab_widget.widget(i)
                if w is not None:
                    return w
        # No tabs — create a placeholder one with unique id
        import uuid
        return self.output_tabs.add_run_tab(
            f"sys-{uuid.uuid4().hex[:8]}", "输出", self.process_manager)

    def _on_check_dependencies(self):
        """Handle check dependencies button click - with caching."""
        selected_items = self.tree_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请选择要检测的脚本")
            return

        item = selected_items[0]
        script_id = item.data(0, Qt.ItemDataRole.UserRole)

        if not script_id:
            QMessageBox.warning(self, "警告", "请选择有效的脚本")
            return

        script = self.python_service.get_script(script_id)
        script_name = script.get("name", f"脚本{script_id}") if script else f"脚本{script_id}"
        out = self._get_active_output()
        out.append_output(f"正在检测脚本「{script_name}」的依赖...\n")

        # Use cached installed packages (valid for 5 minutes)
        import time
        current_time = time.time()
        if self._installed_packages_cache is None or (current_time - self._packages_cache_time) > 300:
            self._installed_packages_cache = self.dependency_service._get_installed_packages()
            self._packages_cache_time = current_time

        missing = self.dependency_service.check_missing(script_id)

        if missing:
            missing_str = ", ".join(missing)
            self._get_active_output().append_output(f"缺失的依赖：{missing_str}")
            QMessageBox.warning(
                self,
                "依赖检测",
                f"脚本缺失以下依赖:\n{missing_str}"
            )
        else:
            self._get_active_output().append_output("所有依赖已满足")
            QMessageBox.information(
                self,
                "依赖检测",
                "所有依赖已满足"
            )

    def _on_refresh(self):
        """Handle refresh button click - sync scripts from directory and refresh tree."""
        # Get scripts_dir from config service if available (for updated paths)
        scripts_dir = None
        if hasattr(self, 'config_service') and self.config_service:
            scripts_dir = self.config_service.get("paths.scripts_dir", "")
            if scripts_dir and scripts_dir.strip() and os.path.exists(scripts_dir):
                # Update scripts_dir before syncing
                self.python_service.set_scripts_dir(scripts_dir)

        # Sync scripts from directory
        if self.python_service.scripts_dir:
            synced = self.python_service.sync_scripts_from_dir()
            if synced > 0:
                QMessageBox.information(
                    self,
                    "同步完成",
                    f"已从目录同步 {synced} 个脚本到数据库"
                )

        # Refresh tree view
        self._refresh_tree()
        self._get_active_output().append_output("脚本列表已刷新")

    def _on_download_whl(self):
        """Handle download WHL button click."""
        dialog = WheelDownloadDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            package_name = dialog.get_package_name()
            download_path = dialog.get_download_path()

            if not package_name or not download_path:
                return

            # Execute pip download
            import subprocess
            self._get_active_output().append_output(f"正在下载 {package_name}...")
            self._get_active_output().append_output(f"命令：pip download -d {download_path} {package_name}")

            try:
                result = subprocess.run(
                    ["pip", "download", "-d", download_path, package_name],
                    capture_output=True,
                    text=True,
                    timeout=120
                )

                if result.returncode == 0:
                    self._get_active_output().append_output(f"下载成功：{package_name}")
                    self._get_active_output().append_output(result.stdout)
                    QMessageBox.information(
                        self,
                        "下载成功",
                        f"{package_name} 已下载到:\n{download_path}"
                    )
                else:
                    self._get_active_output().append_output(f"下载失败：{result.stderr}")

                    # Parse error message for user-friendly display
                    error_msg = result.stderr.strip()
                    if "Could not find a version that satisfies the requirement" in error_msg:
                        friendly_msg = f"找不到包 '{package_name}'\n\n" \
                                       f"可能的原因：\n" \
                                       f"1. 包名拼写错误\n" \
                                       f"2. 该包在 PyPI 上不存在\n" \
                                       f"3. 该包与当前 Python 版本不兼容"
                        QMessageBox.critical(self, "下载失败", friendly_msg)
                    elif "No matching distribution found" in error_msg:
                        friendly_msg = f"未找到匹配的包版本\n\n" \
                                       f"请检查：\n" \
                                       f"1. 包名是否正确\n" \
                                       f"2. 当前 Python 版本是否支持该包"
                        QMessageBox.critical(self, "下载失败", friendly_msg)
                    else:
                        QMessageBox.critical(
                            self,
                            "下载失败",
                            f"下载 {package_name} 失败:\n{error_msg}"
                        )
            except subprocess.TimeoutExpired:
                self._get_active_output().append_output("下载超时")
                QMessageBox.warning(self, "下载超时", "下载操作超时，请检查网络连接")
            except Exception as e:
                self._get_active_output().append_output(f"错误：{str(e)}")
                QMessageBox.critical(self, "下载错误", f"下载失败:\n{str(e)}")

    def set_scripts_dir(self, path: str):
        """Set the scripts directory for PythonService.

        Args:
            path: Path to the scripts directory
        """
        self.python_service.set_scripts_dir(path)

    def set_config_service(self, config_service):
        """Set the config service for getting updated paths.

        Args:
            config_service: ConfigService instance
        """
        self.config_service = config_service


class WheelDownloadDialog(QDialog):
    """Dialog for downloading wheel files."""

    def __init__(self, parent=None):
        """Initialize the wheel download dialog.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.config_service = None
        self.current_python_version = self._get_python_version()
        self._load_config_service()
        self._setup_ui()
        self._load_last_path()


class ScriptPropertiesDialog(QDialog):
    """Dialog for displaying script properties."""

    def __init__(self, parent=None, script_data=None):
        """Initialize the script properties dialog.

        Args:
            parent: Parent widget
            script_data: Script data dictionary
        """
        super().__init__(parent)
        self.script_data = script_data or {}
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("脚本属性")
        self.setMinimumSize(500, 400)
        self.setModal(True)

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Properties form (read-only)
        form_layout = QVBoxLayout()
        form_layout.setSpacing(10)

        # ID
        id_row, self.id_label = self._create_property_row("脚本 ID:", "")
        form_layout.addLayout(id_row)

        # Name
        name_row, self.name_label = self._create_property_row("脚本名称:", "")
        form_layout.addLayout(name_row)

        # Description
        desc_row, self.desc_label = self._create_property_row("功能描述:", "")
        self.desc_label.setWordWrap(True)
        form_layout.addLayout(desc_row)

        # File path
        path_row, self.path_label = self._create_property_row("文件路径:", "")
        self.path_label.setWordWrap(True)
        form_layout.addLayout(path_row)

        # Created at
        created_row, self.created_label = self._create_property_row("创建时间:", "")
        form_layout.addLayout(created_row)

        # Updated at
        updated_row, self.updated_label = self._create_property_row("修改时间:", "")
        form_layout.addLayout(updated_row)

        layout.addLayout(form_layout)

        # Code preview
        code_label = QLabel("代码预览:")
        code_label.setStyleSheet("QLabel { font-weight: bold; margin-top: 10px; }")
        layout.addWidget(code_label)

        self.code_preview = QTextEdit()
        self.code_preview.setFont(QFont("Consolas", 9))
        self.code_preview.setReadOnly(True)
        self.code_preview.setMaximumHeight(200)
        layout.addWidget(self.code_preview)

        # Close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        close_btn = QPushButton("关闭")
        close_btn.setFixedWidth(100)
        close_btn.setDefault(True)
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def _create_property_row(self, label_text, value_text):
        """Create a property row with label and value.

        Args:
            label_text: Label text
            value_text: Initial value text

        Returns:
            Tuple of (QHBoxLayout, value_label)
        """
        row_layout = QHBoxLayout()
        row_layout.setSpacing(10)

        label = QLabel(label_text)
        label.setFixedWidth(80)
        label.setStyleSheet("QLabel { font-weight: bold; color: #555; }")
        row_layout.addWidget(label)

        value_label = QLabel(value_text)
        value_label.setStyleSheet("QLabel { color: #333; padding: 5px; background-color: #f9f9f9; border: 1px solid #ddd; border-radius: 3px; }")
        value_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        row_layout.addWidget(value_label)

        return row_layout, value_label

    def _load_data(self):
        """Load script data into the dialog."""
        self.id_label.setText(str(self.script_data.get("id", "")))
        self.name_label.setText(self.script_data.get("name", ""))
        self.desc_label.setText(self.script_data.get("description", "") or "(无)")
        self.path_label.setText(self.script_data.get("file_path", "") or "(无)")
        self.created_label.setText(self.script_data.get("created_at", "") or "(无)")
        self.updated_label.setText(self.script_data.get("updated_at", "") or "(无)")
        self.code_preview.setPlainText(self.script_data.get("code", ""))


class WheelDownloadDialog(QDialog):
    """Dialog for downloading wheel files."""

    def __init__(self, parent=None):
        """Initialize the wheel download dialog.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.config_service = None
        self.current_python_version = self._get_python_version()
        self._load_config_service()
        self._setup_ui()
        self._load_last_path()

    def _get_python_version(self):
        """Get current Python version.

        Returns:
            Python version string (e.g., '3.10.9')
        """
        import sys
        version = sys.version_info
        return f"{version.major}.{version.minor}.{version.micro}"

    def _validate_package_name(self, name: str) -> tuple:
        """Validate package name.

        Args:
            name: Package name to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        import re

        if not name:
            return False, "请输入包名"

        # PEP 503 package name pattern
        if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?$|^[a-zA-Z0-9]$', name):
            return False, f"无效的包名：'{name}'\n\n包名只能包含字母、数字、下划线、连字符和点"

        # Reject names that are just numbers
        if re.match(r'^\d+$', name):
            return False, f"无效的包名：'{name}'\n\n包名不能是纯数字"

        # Reject names starting with hyphen, underscore, or dot
        if name[0] in '-_.':
            return False, f"无效的包名：'{name}'\n\n包名不能以 '{name[0]}' 开头"

        return True, ""

    def _load_config_service(self):
        """Load config service to get/save last download path."""
        try:
            import os
            from core.config_service import ConfigService
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                'data', 'config.json'
            )
            self.config_service = ConfigService(config_path)
            self.config_service.load()
        except Exception:
            self.config_service = None

    def _setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("下载 WHL 文件包")
        self.setMinimumSize(550, 280)
        self.setModal(True)

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Package name field
        pkg_layout = QHBoxLayout()
        pkg_label = QLabel("三方库名称:")
        pkg_label.setFixedWidth(100)
        self.pkg_input = QLineEdit()
        self.pkg_input.setPlaceholderText("例如：requests, numpy, pandas")
        pkg_layout.addWidget(pkg_label)
        pkg_layout.addWidget(self.pkg_input)
        layout.addLayout(pkg_layout)

        # Download path field
        path_layout = QHBoxLayout()
        path_label = QLabel("下载路径:")
        path_label.setFixedWidth(100)
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("选择 WHL 文件保存目录")
        path_layout.addWidget(path_label)
        path_layout.addWidget(self.path_input)

        # Browse button
        browse_btn = QPushButton("浏览...")
        browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(self._on_browse)
        path_layout.addWidget(browse_btn)
        layout.addLayout(path_layout)

        # Python version info
        version_label = QLabel(
            f"当前 Python 版本：{self.current_python_version}\n"
            f"请确保下载环境的 Python 版本与使用环境一致"
        )
        version_label.setStyleSheet("QLabel { color: #d83b01; font-weight: bold; }")
        version_label.setWordWrap(True)
        layout.addWidget(version_label)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedWidth(100)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        download_btn = QPushButton("下载")
        download_btn.setFixedWidth(100)
        download_btn.setDefault(True)
        download_btn.setStyleSheet("""
            QPushButton {
                background-color: #009900;
                color: white;
                border: none;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #008800;
            }
        """)
        download_btn.clicked.connect(self._on_download)
        button_layout.addWidget(download_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def _load_last_path(self):
        """Load last used download path from config."""
        if self.config_service:
            last_path = self.config_service.get("paths.last_whl_download_path", "")
            if last_path:
                self.path_input.setText(last_path)

    def _save_last_path(self, path):
        """Save download path to config."""
        if self.config_service:
            self.config_service.set("paths.last_whl_download_path", path)
            self.config_service.save()

    def _on_browse(self):
        """Handle browse button click."""
        path = QFileDialog.getExistingDirectory(
            self,
            "选择 WHL 文件保存目录",
            self.path_input.text() or "",
            QFileDialog.Option.ShowDirsOnly
        )
        if path:
            self.path_input.setText(path)

    def _on_download(self):
        """Handle download button click."""
        package_name = self.pkg_input.text().strip()

        # Validate package name
        is_valid, error_msg = self._validate_package_name(package_name)
        if not is_valid:
            QMessageBox.warning(self, "包名无效", error_msg)
            return

        download_path = self.path_input.text().strip()
        if not download_path:
            QMessageBox.warning(self, "警告", "请选择下载路径")
            return

        # Save path for next use
        self._save_last_path(download_path)

        self.accept()

    def get_package_name(self):
        """Get the package name.

        Returns:
            Package name string
        """
        return self.pkg_input.text().strip()

    def get_download_path(self):
        """Get the download path.

        Returns:
            Download path string
        """
        return self.path_input.text().strip()
