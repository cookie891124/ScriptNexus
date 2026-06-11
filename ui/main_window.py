"""MainWindow - Main window for the Script Manager application."""

import os
import sqlite3
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QStackedWidget, QHBoxLayout, QMessageBox
from PyQt6.QtCore import pyqtSignal

from ui.components.nav_bar import NavBar
from ui.components.toolbar import ToolBar
from ui.components.dashboard import Dashboard
from ui.system_tray import SystemTray
from ui.dialogs.settings_dialog import SettingsDialog


class MainWindow(QMainWindow):
    """Main application window integrating NavBar, ToolBar, and Dashboard.

    Features:
        - Left navigation bar (NavBar)
        - Top toolbar (ToolBar)
        - Content area with QStackedWidget for multi-page management
        - System tray integration

    Signals:
        navigation_requested: Emitted when navigation is requested
        import_requested: Emitted when import action is triggered
        export_requested: Emitted when export action is triggered
    """

    navigation_requested = pyqtSignal(str)
    import_requested = pyqtSignal()
    export_requested = pyqtSignal()

    def __init__(self, parent=None):
        """Initialize the main window.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("ScriptNexus")
        self.setMinimumSize(1100, 720)
        self.resize(1280, 820)

        # Initialize services for settings dialog
        self.path_detection_service = None
        self.config_service = None
        self.deployment_service = None
        self.import_export_service = None

        # Paths (will be set by set_paths, use current directory as default)
        base_dir = os.path.dirname(os.path.dirname(__file__))
        self.db_path = None  # Will be set by set_paths
        self.scripts_dir = os.path.join(base_dir, 'scripts')
        self.whl_pool_dir = os.path.join(base_dir, 'whl_pool')
        self.templates_dir = os.path.join(base_dir, 'templates')

        # Module instances (lazy initialized)
        self.python_module = None
        self.wps_module = None
        self.js_module = None

        self._setup_ui()
        self.nav_bar.navigate_to(NavBar.DASHBOARD)
        self._setup_system_tray()
        self._connect_signals()

    def set_services(self, path_detection_service, config_service, deployment_service=None):
        """Set services for settings dialog and modules.

        Args:
            path_detection_service: PathDetectionService instance
            config_service: ConfigService instance
            deployment_service: DeploymentService instance (optional)
        """
        self.path_detection_service = path_detection_service
        self.config_service = config_service
        self.deployment_service = deployment_service

        # Load paths from config if available
        self._load_paths_from_config()
        self._update_tray_paths()

        # Refresh dashboard stats on initial load
        self._refresh_dashboard()

    def set_paths(self, scripts_dir, whl_pool_dir, templates_dir, db_path=None):
        """Set application path 和 update modules.

        Args:
            scripts_dir: Path to scripts directory
            whl_pool_dir: Path to WHL pool directory
            templates_dir: Path to templates directory
            db_path: Path to database file (optional)
        """
        self.scripts_dir = scripts_dir
        self.whl_pool_dir = whl_pool_dir
        self.templates_dir = templates_dir
        self.db_path = db_path

        # Load WPS startup paths from config
        word_startup = self.config_service.get("paths.wps_word_startup", "") if self.config_service else ""
        excel_startup = self.config_service.get("paths.wps_excel_startup", "") if self.config_service else ""

        # Update modules with paths
        if self.python_module and scripts_dir and scripts_dir.strip():
            self.python_module.set_scripts_dir(scripts_dir)
        if self.wps_module:
            self.wps_module.set_paths(templates_dir, word_startup, excel_startup)

        # Update deployment service paths and template dirs
        if self.deployment_service:
            if self.deployment_service.wps_service:
                self.deployment_service.wps_service.set_paths(templates_dir, word_startup, excel_startup)
            self.deployment_service.word_template_dir = word_startup if word_startup and word_startup.strip() else ""
            self.deployment_service.excel_template_dir = excel_startup if excel_startup and excel_startup.strip() else ""

    def _load_paths_from_config(self):
        """Load paths from config service if available."""
        if not self.config_service:
            return

        # Use get_path to validate that paths exist before using them
        scripts_dir = self.config_service.get_path("paths.scripts_dir", "")
        whl_pool_dir = self.config_service.get_path("paths.whl_pool_dir", "")
        templates_dir = self.config_service.get_path("paths.templates_dir", "")

        # Use config paths if set and exist, otherwise use defaults
        if scripts_dir and scripts_dir.strip() and os.path.exists(scripts_dir):
            self.scripts_dir = scripts_dir
        if whl_pool_dir and whl_pool_dir.strip() and os.path.exists(whl_pool_dir):
            self.whl_pool_dir = whl_pool_dir
        if templates_dir and templates_dir.strip() and os.path.exists(templates_dir):
            self.templates_dir = templates_dir

    def _setup_ui(self):
        """Set up the main window UI."""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Toolbar
        self.toolbar = ToolBar()
        main_layout.addWidget(self.toolbar)

        # Content area (NavBar + Pages)
        content_widget = QWidget()
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Navigation bar
        self.nav_bar = NavBar()
        content_layout.addWidget(self.nav_bar)

        # Stacked widget for pages
        self.stack = QStackedWidget()
        self.stack.setObjectName("contentStack")
        self.stack.setStyleSheet("QStackedWidget#contentStack { background: #F5F6FA; }")

        # Add pages - use placeholder widgets, modules initialized on demand
        self.dashboard = Dashboard()
        self.stack.addWidget(self.dashboard)

        # Python module page - placeholder
        self.python_page = QWidget()
        py_layout = QVBoxLayout()
        py_layout.setContentsMargins(0, 0, 0, 0)
        self.python_page.setLayout(py_layout)
        self.stack.addWidget(self.python_page)

        # WPS module page - placeholder
        self.wps_page = QWidget()
        wps_layout = QVBoxLayout()
        wps_layout.setContentsMargins(0, 0, 0, 0)
        self.wps_page.setLayout(wps_layout)
        self.stack.addWidget(self.wps_page)

        # JS module page - placeholder
        self.js_page = QWidget()
        js_layout = QVBoxLayout()
        js_layout.setContentsMargins(0, 0, 0, 0)
        self.js_page.setLayout(js_layout)
        self.stack.addWidget(self.js_page)

        # Eliminate QStackedLayout's default 9px margins (must do after adding pages)
        self.stack.layout().setContentsMargins(0, 0, 0, 0)

        content_layout.addWidget(self.stack)
        content_widget.setLayout(content_layout)

        main_layout.addWidget(content_widget)
        central_widget.setLayout(main_layout)

    def _init_python_module(self):
        """Initialize Python module if not already initialized."""
        if self.python_module is not None:
            return

        from ui.modules.python_module import PythonModule
        db_path = self.db_path if hasattr(self, 'db_path') and self.db_path else None
        if not db_path:
            from core.platform_utils import get_app_data_dir
            db_path = os.path.join(get_app_data_dir(), 'scripts.db')
        self.python_module = PythonModule(db_path, self.whl_pool_dir)

        # Set config service for getting updated paths
        if self.config_service:
            self.python_module.set_config_service(self.config_service)

        if self.scripts_dir:
            self.python_module.set_scripts_dir(self.scripts_dir)
            # Sync scripts from directory on first load
            self.python_module.python_service.sync_scripts_from_dir()

        # Connect signals for dashboard update
        self.python_module.script_added.connect(self._on_script_changed)
        self.python_module.script_deleted.connect(self._on_script_changed)

        # Replace the placeholder widget content
        self._replace_page_content(self.python_page, self.python_module)

    def _init_wps_module(self):
        """Initialize WPS module if not already initialized."""
        if self.wps_module is not None:
            return

        from ui.modules.wps_module import WpsModule
        db_path = self.db_path if hasattr(self, 'db_path') and self.db_path else None
        if not db_path:
            from core.platform_utils import get_app_data_dir
            db_path = os.path.join(get_app_data_dir(), 'scripts.db')
        self.wps_module = WpsModule(db_path)

        # Load WPS startup paths from config
        word_startup = self.config_service.get("paths.wps_word_startup", "") if self.config_service else ""
        excel_startup = self.config_service.get("paths.wps_excel_startup", "") if self.config_service else ""

        if self.templates_dir:
            self.wps_module.set_paths(self.templates_dir, word_startup, excel_startup)

        # Pass deployment service for WPS deploy button
        self.wps_module.deployment_service = self.deployment_service

        # Connect signals for dashboard update
        self.wps_module.script_added.connect(self._on_script_changed)
        self.wps_module.script_deleted.connect(self._on_script_changed)

        # Replace the placeholder widget content
        self._replace_page_content(self.wps_page, self.wps_module)

    def _init_js_module(self):
        """Initialize JS module if not already initialized."""
        if self.js_module is not None:
            return

        from ui.modules.js_module import JsModule
        db_path = self.db_path if hasattr(self, 'db_path') and self.db_path else None
        if not db_path:
            from core.platform_utils import get_app_data_dir
            db_path = os.path.join(get_app_data_dir(), 'scripts.db')
        self.js_module = JsModule(db_path)

        # Connect signals for dashboard update
        self.js_module.script_added.connect(self._on_script_changed)
        self.js_module.script_deleted.connect(self._on_script_changed)

        # Replace the placeholder widget content
        self._replace_page_content(self.js_page, self.js_module)

    def _replace_page_content(self, page_widget, new_widget):
        """Replace the content of a page widget.

        Args:
            page_widget: The page container widget
            new_widget: The new widget to add
        """
        layout = page_widget.layout()
        # Clear existing widgets
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        layout.addWidget(new_widget)

    def _connect_signals(self):
        """Connect all signals."""
        # NavBar signals
        self.nav_bar.navigation_requested.connect(self._on_navigation_requested)
        self.nav_bar.navigation_requested.connect(self.navigation_requested.emit)

        # ToolBar signals
        self.toolbar.import_requested.connect(self._on_import_requested)
        self.toolbar.export_requested.connect(self._on_export_requested)
        self.toolbar.settings_requested.connect(self._on_settings_requested)

        # System tray signals
        self._update_tray_paths()

    def _update_tray_paths(self):
        """Pass current paths to system tray quick-entry menu."""
        if hasattr(self, 'system_tray'):
            scripts_dir = self.config_service.get("paths.scripts_dir", "") if self.config_service else self.scripts_dir
            word_startup = self.config_service.get("paths.wps_word_startup", "") if self.config_service else ""
            excel_startup = self.config_service.get("paths.wps_excel_startup", "") if self.config_service else ""
            chrome_bookmarks = self.config_service.get("paths.chrome_bookmarks", "") if self.config_service else ""
            self.system_tray.set_paths(
                python_scripts=scripts_dir,
                wps_word=word_startup,
                wps_excel=excel_startup,
                chrome_bookmarks=chrome_bookmarks,
            )

    def _setup_system_tray(self):
        """Set up the system tray integration."""
        self.system_tray = SystemTray()
        self.system_tray.show_main_window.connect(self._on_show_main_window)
        self.system_tray.quit_triggered.connect(self.close)

    def _on_navigation_requested(self, name):
        """Handle navigation request.

        Args:
            name: Target page name
        """
        # Map navigation names to page indices
        page_map = {
            NavBar.DASHBOARD: 0,
            NavBar.PYTHON_SCRIPTS: 1,
            NavBar.WPS_SCRIPTS: 2,
            NavBar.JS_SCRIPTS: 3
        }
        index = page_map.get(name, 0)

        # Initialize module before showing (lazy initialization)
        if index == 1:
            self._init_python_module()
        elif index == 2:
            self._init_wps_module()
        elif index == 3:
            self._init_js_module()

        self.stack.setCurrentIndex(index)

        # Update nav bar visual state
        self.nav_bar.navigate_to(name)

        # Refresh dashboard when switching to dashboard page
        if index == 0:
            self._refresh_dashboard()

    def _on_show_main_window(self):
        """Handle show main window request from system tray."""
        self.show()
        self.activateWindow()
        self.raise_()

    def _on_settings_requested(self):
        """Handle settings button click."""
        if self.path_detection_service and self.config_service:
            dialog = SettingsDialog(
                self.path_detection_service,
                self.config_service,
                self
            )
            if dialog.exec() == SettingsDialog.DialogCode.Accepted:
                # Reload paths from config and update modules
                self._reload_paths_from_config()

    def _on_export_requested(self):
        """Handle export button click."""
        from ui.dialogs.export_dialog import ExportDialog

        dlg = ExportDialog(
            scripts_dir=self.scripts_dir,
            templates_dir=self.templates_dir,
            db_path=self.db_path,
            parent=self,
        )
        if dlg.exec() != ExportDialog.DialogCode.Accepted:
            return

        selections = dlg.get_selections()
        output_path = selections.pop('output_path')

        if not self.import_export_service:
            QMessageBox.warning(self, "错误", "导入/导出服务未初始化，请重启应用")
            return

        result = self.import_export_service.export_package_with_selection(
            selections, output_path
        )

        if result['success']:
            counts_str = ', '.join(f'{k}: {v}' for k, v in result.get('counts', {}).items() if v)
            QMessageBox.information(
                self, "导出成功",
                f"已导出到:\n{output_path}\n\n导出统计:\n{counts_str}"
            )
        else:
            QMessageBox.warning(self, "导出失败", result.get('error', '未知错误'))

    def _on_import_requested(self):
        """Handle import button click."""
        from ui.dialogs.import_dialog import ImportDialog

        if not self.import_export_service:
            QMessageBox.warning(self, "错误", "导入/导出服务未初始化，请重启应用")
            return

        dlg = ImportDialog(
            scripts_dir=self.scripts_dir,
            templates_dir=self.templates_dir,
            db_path=self.db_path,
            parent=self,
        )
        if dlg.exec() != ImportDialog.DialogCode.Accepted:
            return

        options = dlg.get_import_options()

        reply = QMessageBox.question(
            self, "确认导入",
            f"即将导入文件:\n{options['zip_path']}\n\n"
            f"模式: {'覆盖' if options['mode'] == 'overwrite' else '新增'}\n\n"
            f"导入后将刷新当前页面。是否继续?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        result = self.import_export_service.import_package_with_options(
            options['zip_path'], options['mode']
        )

        if result['success']:
            imported = '\n'.join(f"  ✓ {item}" for item in result['imported'])
            QMessageBox.information(
                self, "导入成功",
                f"已导入:\n{imported}\n\n正在刷新..."
            )
            # Reload config and refresh all modules
            self._reload_paths_from_config()
            self._refresh_modules()
            self._refresh_dashboard()
        else:
            QMessageBox.warning(self, "导入失败", result.get('error', '未知错误'))

    def _reload_paths_from_config(self):
        """Reload paths from config service and update modules."""
        if not self.config_service:
            return

        scripts_dir = self.config_service.get("paths.scripts_dir", "")
        whl_pool_dir = self.config_service.get("paths.whl_pool_dir", "")
        templates_dir = self.config_service.get("paths.templates_dir", "")
        chrome_bookmarks = self.config_service.get("paths.chrome_bookmarks", "")
        word_startup = self.config_service.get("paths.wps_word_startup", "")
        excel_startup = self.config_service.get("paths.wps_excel_startup", "")

        # Update paths (only when path is non-empty)
        if scripts_dir and scripts_dir.strip():
            self.set_paths(scripts_dir, whl_pool_dir, templates_dir)

        # Update deployment service paths and template dirs
        if self.deployment_service:
            if self.deployment_service.wps_service:
                self.deployment_service.wps_service.set_paths(templates_dir, word_startup, excel_startup)
            self.deployment_service.word_template_dir = word_startup if word_startup and word_startup.strip() else ""
            self.deployment_service.excel_template_dir = excel_startup if excel_startup and excel_startup.strip() else ""

        # Update JS module chrome path
        if self.js_module and chrome_bookmarks and chrome_bookmarks.strip():
            self.js_module.set_chrome_path(chrome_bookmarks)

        # Refresh module displays
        self._refresh_modules()
        self._update_tray_paths()

    def _refresh_modules(self):
        """Refresh all modules to reflect new paths."""
        # Refresh Python module - sync from new directory first
        if self.python_module:
            # Update scripts_dir from config
            scripts_dir = self.config_service.get("paths.scripts_dir", "") if self.config_service else ""
            if scripts_dir and scripts_dir.strip() and os.path.exists(scripts_dir):
                self.python_module.set_scripts_dir(scripts_dir)
                # Sync scripts from the new directory
                self.python_module.python_service.sync_scripts_from_dir()
            self.python_module._refresh_tree()

        # Refresh WPS module
        if self.wps_module:
            self.wps_module._refresh_all()

        # Refresh JS module
        if self.js_module:
            self.js_module._refresh_list()

    def _on_script_changed(self):
        """Handle script change (added/deleted) - refresh dashboard."""
        self._refresh_dashboard()

    def _refresh_dashboard(self):
        """Refresh dashboard statistics."""
        # Use the db_path from set_paths() or get from platform utils
        if hasattr(self, 'db_path') and self.db_path:
            db_path = self.db_path
        else:
            # Fallback: use platform utils to get correct path
            from core.platform_utils import get_app_data_dir
            data_dir = get_app_data_dir()
            db_path = os.path.join(data_dir, 'scripts.db')

        # Ensure database exists and has tables
        if not os.path.exists(db_path):
            # Database doesn't exist yet, show zero stats
            self.dashboard.update_stats(0, 0, 0)
            return

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        try:
            # Count Python scripts from scripts table
            cursor.execute("SELECT COUNT(*) FROM scripts")
            python_count = cursor.fetchone()[0]

            # Count WPS scripts from wps_scripts table
            cursor.execute("SELECT COUNT(*) FROM wps_scripts")
            wps_count = cursor.fetchone()[0]

            # Count JS scripts from js_scripts table
            cursor.execute("SELECT COUNT(*) FROM js_scripts")
            js_count = cursor.fetchone()[0]
        except sqlite3.OperationalError:
            # Tables don't exist yet, show zero stats
            python_count = 0
            wps_count = 0
            js_count = 0

        conn.close()

        self.dashboard.update_stats(python_count, wps_count, js_count)

    def update_dashboard_stats(self, python_count, wps_count, js_count):
        """Update the dashboard statistics.

        Args:
            python_count: Number of Python scripts
            wps_count: Number of WPS scripts
            js_count: Number of JS scripts
        """
        self.dashboard.update_stats(python_count, wps_count, js_count)

    def closeEvent(self, event):
        """Handle close event - minimize to tray instead of quitting.

        Args:
            event: QCloseEvent
        """
        # Check if user explicitly requested quit (via tray menu)
        # If so, allow the window to close and quit the application
        if hasattr(self, '_force_close') and self._force_close:
            event.accept()
            return

        # Hide the window instead of closing for normal close requests
        self.hide()
        event.ignore()
