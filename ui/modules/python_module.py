"""PythonModule - Python script management module with tree view and code editor."""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTreeWidget,
    QTreeWidgetItem, QTextEdit, QLabel, QDialog, QLineEdit,
    QMessageBox, QSplitter, QFrame, QToolBar, QFileDialog, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QProcess, QProcessEnvironment, QObject
from PyQt6.QtGui import QFont, QIcon, QAction, QTextCursor

from services.python_service import PythonService
from services.dependency_service import DependencyService


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


class InteractiveOutputWidget(QWidget):
    """Interactive output widget with display area and input line."""

    # Signals
    input_sent = pyqtSignal(str)  # User input submitted

    def __init__(self, parent=None):
        """Initialize the interactive output widget."""
        super().__init__(parent)
        self._is_running = False
        self._setup_ui()

    def _setup_ui(self):
        """Set up the widget UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)

        # Output display (read-only)
        self.output_display = QTextEdit()
        self.output_display.setReadOnly(True)
        self.output_display.setFont(QFont("Consolas", 10))
        self.output_display.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #333;
                border-radius: 3px;
                padding: 5px;
            }
        """)
        self.output_display.setPlaceholderText("运行结果将显示在这里...")
        self.output_display.setMinimumHeight(80)
        layout.addWidget(self.output_display)

        # Input line
        self.input_line = QLineEdit()
        self.input_line.setFont(QFont("Consolas", 10))
        self.input_line.setPlaceholderText("输入内容后按 Enter 发送...")
        self.input_line.setEnabled(False)  # Disabled by default
        self.input_line.setStyleSheet("""
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
        """)
        self.input_line.returnPressed.connect(self._on_input_submit)
        layout.addWidget(self.input_line)

        self.setLayout(layout)

    def append_output(self, text: str, is_error: bool = False):
        """Append text to output display with auto-scroll.

        Args:
            text: Text to append
            is_error: If True, show in red color (for stderr)
        """
        # Move cursor to end for appending
        cursor = self.output_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.output_display.setTextCursor(cursor)

        if is_error:
            # Insert with red color using HTML
            self.output_display.insertHtml(f'<span style="color: #f44;">{text}</span>')
        else:
            # Insert plain text
            self.output_display.insertPlainText(text)

        # Ensure scroll to bottom
        self.output_display.ensureCursorVisible()

    def set_running_mode(self, is_running: bool):
        """Enable/disable input line based on script running state.

        Args:
            is_running: True if script is running, False otherwise
        """
        self._is_running = is_running
        self.input_line.setEnabled(is_running)
        if is_running:
            self.input_line.setFocus()
        else:
            self.input_line.clear()

    def clear_output(self):
        """Clear the output display."""
        self.output_display.clear()

    def _on_input_submit(self):
        """Handle Enter key in input line."""
        if not self._is_running:
            return
        text = self.input_line.text()
        if text:
            self.input_sent.emit(text)
            self.input_line.clear()
            # Show user input in output with prompt style
            self.append_output(f"> {text}\n")


class ScriptProcessManager(QObject):
    """Manages QProcess for script execution with real-time output."""

    # Signals
    output_received = pyqtSignal(str)      # stdout data
    error_received = pyqtSignal(str)       # stderr data
    process_started = pyqtSignal()
    process_finished = pyqtSignal(int, int)  # exitCode, exitStatus
    input_required = pyqtSignal()          # Script may need input

    def __init__(self, parent=None):
        """Initialize the script process manager."""
        super().__init__(parent)
        self.process: QProcess = None
        self.temp_file_path: str = None
        self._is_temp: bool = False

    def start_script(self, script_path: str, working_dir: str,
                     script_dir: str = "", is_temp: bool = False):
        """Start script execution with QProcess.

        Args:
            script_path: Path to the Python script file
            working_dir: Working directory for execution
            script_dir: Original script directory (added to PYTHONPATH)
            is_temp: Whether script_path is a temporary file
        """
        # Clean up previous process
        if self.process:
            if self.process.state() != QProcess.ProcessState.NotRunning:
                self.process.kill()
            self.process.deleteLater()

        self.process = QProcess(self)
        self.process.setWorkingDirectory(working_dir)
        self.temp_file_path = script_path if is_temp else None
        self._is_temp = is_temp

        # Set environment to force UTF-8 encoding on Windows
        env = QProcessEnvironment.systemEnvironment()
        # Force Python to use UTF-8 for stdout/stderr
        env.insert("PYTHONIOENCODING", "utf-8")
        # Add original script directory to PYTHONPATH so sibling
        # modules (e.g. db_utils.py) can be imported
        if script_dir:
            existing = env.value("PYTHONPATH", "")
            if existing:
                env.insert("PYTHONPATH", script_dir + os.pathsep + existing)
            else:
                env.insert("PYTHONPATH", script_dir)
        self.process.setProcessEnvironment(env)

        # Connect signals
        self.process.readyReadStandardOutput.connect(self._on_stdout_ready)
        self.process.readyReadStandardError.connect(self._on_stderr_ready)
        self.process.started.connect(self._on_process_started)
        self.process.finished.connect(self._on_process_finished)
        self.process.errorOccurred.connect(self._on_process_error)

        # Start process - use python with script path as argument
        self.process.start("python", [script_path])

    def send_input(self, text: str):
        """Send user input to the running process stdin.

        Args:
            text: User input text
        """
        if self.process and self.process.state() == QProcess.ProcessState.Running:
            # Write to stdin with newline (Python input() expects newline)
            data = (text + "\n").encode('utf-8')
            self.process.write(data)

    def stop(self):
        """Stop the running process."""
        if self.process:
            if self.process.state() == QProcess.ProcessState.Running:
                self.process.kill()
            # Clean up temp file immediately
            self._cleanup_temp_file()

    def is_running(self) -> bool:
        """Check if process is running.

        Returns:
            True if process is running, False otherwise
        """
        return self.process and self.process.state() == QProcess.ProcessState.Running

    def _on_stdout_ready(self):
        """Handle stdout data available."""
        data = self.process.readAllStandardOutput()
        text = bytes(data).decode('utf-8', errors='replace')
        self.output_received.emit(text)

        # Detect input prompts (e.g., trailing colon or question mark)
        if self._detect_input_prompt(text):
            self.input_required.emit()

    def _on_stderr_ready(self):
        """Handle stderr data available."""
        data = self.process.readAllStandardError()
        text = bytes(data).decode('utf-8', errors='replace')
        self.error_received.emit(text)

    def _on_process_started(self):
        """Handle process started."""
        self.process_started.emit()

    def _on_process_finished(self, exit_code: int, exit_status: int):
        """Handle process finished.

        Args:
            exit_code: Process exit code
            exit_status: QProcess.ExitStatus value
        """
        # Clean up temp file
        self._cleanup_temp_file()
        self.process_finished.emit(exit_code, exit_status)

    def _on_process_error(self, error: QProcess.ProcessError):
        """Handle process error.

        Args:
            error: QProcess.ProcessError value
        """
        error_names = {
            QProcess.ProcessError.FailedToStart: "启动失败",
            QProcess.ProcessError.Crashed: "进程崩溃",
            QProcess.ProcessError.Timedout: "超时",
            QProcess.ProcessError.WriteError: "写入错误",
            QProcess.ProcessError.ReadError: "读取错误",
            QProcess.ProcessError.UnknownError: "未知错误"
        }
        error_msg = error_names.get(error, "未知错误")
        self.error_received.emit(f"\n进程错误: {error_msg}\n")

    def _detect_input_prompt(self, text: str) -> bool:
        """Detect if text indicates input prompt from Python input().

        Args:
            text: Output text to analyze

        Returns:
            True if likely an input prompt, False otherwise
        """
        text = text.strip()
        if not text:
            return False
        # Common patterns: trailing colon, question mark
        return text.endswith(':') or text.endswith('?') or text.endswith(': ')

    def _cleanup_temp_file(self):
        """Clean up temporary script file (only if it was a temp file)."""
        if self.temp_file_path and self._is_temp:
            try:
                if os.path.exists(self.temp_file_path):
                    os.unlink(self.temp_file_path)
            except Exception:
                pass
            self.temp_file_path = None


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

        # Script process manager for interactive execution
        self.process_manager = ScriptProcessManager(self)
        self.process_manager.output_received.connect(self._on_output_received)
        self.process_manager.error_received.connect(self._on_error_received)
        self.process_manager.process_started.connect(self._on_process_started)
        self.process_manager.process_finished.connect(self._on_process_finished)
        self.process_manager.input_required.connect(self._on_input_required)

        self._setup_ui()

        # Connect interactive output widget input signal to process manager
        self.output_widget.input_sent.connect(self.process_manager.send_input)

        self._refresh_tree()

    def _setup_ui(self):
        """Set up the module UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Title (compact with toolbar)
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(10)

        title_label = QLabel("Python 脚本管理")
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

        self.run_btn = QPushButton("运行")
        self.run_btn.setFixedHeight(35)
        self.run_btn.setStyleSheet(self._get_button_style("#009900"))
        self.run_btn.clicked.connect(self._on_run_script)
        toolbar_layout.addWidget(self.run_btn)

        self.check_deps_btn = QPushButton("检测依赖")
        self.check_deps_btn.setFixedHeight(35)
        self.check_deps_btn.setStyleSheet(self._get_button_style("#8764b8"))
        self.check_deps_btn.clicked.connect(self._on_check_dependencies)
        toolbar_layout.addWidget(self.check_deps_btn)

        self.download_whl_btn = QPushButton("下载 WHL")
        self.download_whl_btn.setFixedHeight(35)
        self.download_whl_btn.setStyleSheet(self._get_button_style("#009900"))
        self.download_whl_btn.clicked.connect(self._on_download_whl)
        toolbar_layout.addWidget(self.download_whl_btn)

        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.setFixedHeight(35)
        self.refresh_btn.setStyleSheet(self._get_button_style("#666666"))
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
        tree_label.setStyleSheet("QLabel { font-weight: bold; padding: 3px; background-color: #e8e8e8; }")
        tree_label.setFixedHeight(25)
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
        editor_label.setStyleSheet("QLabel { font-weight: bold; padding: 3px; background-color: #e8e8e8; }")
        editor_label.setFixedHeight(25)
        editor_layout.addWidget(editor_label)

        self.code_editor = QTextEdit()
        self.code_editor.setFont(QFont("Consolas", 10))
        self.code_editor.setReadOnly(True)
        self.code_editor.setPlaceholderText("选择脚本查看代码...")
        editor_layout.addWidget(self.code_editor)

        # Script info panel (file path and timestamps)
        self.script_info_label = QLabel("")
        self.script_info_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 9px;
                padding: 5px;
                background-color: #f5f5f5;
                border: 1px solid #ddd;
            }
        """)
        self.script_info_label.setWordWrap(True)
        editor_layout.addWidget(self.script_info_label)

        editor_panel.setLayout(editor_layout)

        splitter.addWidget(tree_panel)
        splitter.addWidget(editor_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        layout.addWidget(splitter)

        # Output panel - Interactive output widget
        output_label = QLabel("输出")
        output_label.setStyleSheet("QLabel { font-weight: bold; padding: 3px 5px; background-color: #e8e8e8; }")
        output_label.setFixedHeight(25)
        layout.addWidget(output_label)

        self.output_widget = InteractiveOutputWidget()
        self.output_widget.setMaximumHeight(150)
        self.output_widget.setMinimumHeight(100)
        layout.addWidget(self.output_widget)

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
        """Handle run script button click - runs with QProcess for interactive support."""
        # Check if already running - stop it
        if self.process_manager.is_running():
            # User clicked stop - terminate the running script
            self.output_widget.append_output("\n正在停止脚本...\n")
            self.process_manager.stop()
            self._reset_run_button()
            return

        # Get selected script
        selected_items = self.tree_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请选择要运行的脚本")
            return

        item = selected_items[0]
        script_id = item.data(0, Qt.ItemDataRole.UserRole)

        if not script_id:
            QMessageBox.warning(self, "警告", "请选择有效的脚本")
            return

        # Prepare script file for execution
        exec_info = self.python_service.prepare_script_for_execution(script_id)
        if not exec_info:
            QMessageBox.warning(self, "警告", "脚本不存在")
            return

        script_path = exec_info["path"]
        is_temp = exec_info["is_temp"]
        script_dir = exec_info["script_dir"]

        # Clear output and start
        self.output_widget.clear_output()
        self.output_widget.append_output(f"运行脚本 (ID: {script_id})...\n")

        # Get working directory
        working_dir = self.python_service.get_working_directory()

        # Start process with script dir in PYTHONPATH
        self.process_manager.start_script(
            script_path, working_dir,
            script_dir=script_dir, is_temp=is_temp,
        )

        # Update button to stop mode
        self.run_btn.setText("停止")
        self.run_btn.setStyleSheet(self._get_button_style("#d83b01"))

    def _on_output_received(self, text: str):
        """Handle stdout data from running process."""
        self.output_widget.append_output(text)

    def _on_error_received(self, text: str):
        """Handle stderr data from running process."""
        self.output_widget.append_output(text, is_error=True)

    def _on_process_started(self):
        """Handle process started - enable input line."""
        self.output_widget.set_running_mode(True)

    def _on_process_finished(self, exit_code: int, exit_status: int):
        """Handle process finished - disable input and reset button.

        Args:
            exit_code: Process exit code (0 for success)
            exit_status: QProcess.ExitStatus (0 for normal exit, 1 for crash)
        """
        self.output_widget.set_running_mode(False)
        self._reset_run_button()

        if exit_code == 0:
            self.output_widget.append_output("\n脚本运行完成 (退出码: 0)\n")
        else:
            self.output_widget.append_output(f"\n脚本运行失败 (退出码: {exit_code})\n", is_error=True)

    def _on_input_required(self):
        """Handle input prompt detected - focus input line."""
        self.output_widget.set_running_mode(True)

    def _reset_run_button(self):
        """Reset run button to normal state."""
        self.run_btn.setText("运行")
        self.run_btn.setStyleSheet(self._get_button_style("#009900"))
        self.run_btn.setEnabled(True)

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

        self.output_widget.append_output(f"正在检测脚本 (ID: {script_id}) 的依赖...")

        # Use cached installed packages (valid for 5 minutes)
        import time
        current_time = time.time()
        if self._installed_packages_cache is None or (current_time - self._packages_cache_time) > 300:
            self._installed_packages_cache = self.dependency_service._get_installed_packages()
            self._packages_cache_time = current_time

        missing = self.dependency_service.check_missing(script_id)

        if missing:
            missing_str = ", ".join(missing)
            self.output_widget.append_output(f"缺失的依赖：{missing_str}")
            QMessageBox.warning(
                self,
                "依赖检测",
                f"脚本缺失以下依赖:\n{missing_str}"
            )
        else:
            self.output_widget.append_output("所有依赖已满足")
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
        self.output_widget.append_output("脚本列表已刷新")

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
            self.output_widget.append_output(f"正在下载 {package_name}...")
            self.output_widget.append_output(f"命令：pip download -d {download_path} {package_name}")

            try:
                result = subprocess.run(
                    ["pip", "download", "-d", download_path, package_name],
                    capture_output=True,
                    text=True,
                    timeout=120
                )

                if result.returncode == 0:
                    self.output_widget.append_output(f"下载成功：{package_name}")
                    self.output_widget.append_output(result.stdout)
                    QMessageBox.information(
                        self,
                        "下载成功",
                        f"{package_name} 已下载到:\n{download_path}"
                    )
                else:
                    self.output_widget.append_output(f"下载失败：{result.stderr}")

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
                self.output_widget.append_output("下载超时")
                QMessageBox.warning(self, "下载超时", "下载操作超时，请检查网络连接")
            except Exception as e:
                self.output_widget.append_output(f"错误：{str(e)}")
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
            f"💻 当前 Python 版本：{self.current_python_version}\n"
            f"⚠ 请确保外网 Python 版本与内网版本对齐（使用相同版本下载）"
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
