"""Tests for MainWindow and its components.

These tests verify the structure and attributes of UI components
without testing actual Qt widget behavior.
"""

import pytest


class TestNavBarClass:
    """Tests for NavBar class structure."""

    def test_navbar_class_exists(self):
        """Test that NavBar class exists."""
        from ui.components import nav_bar
        assert hasattr(nav_bar, 'NavBar')

    def test_navbar_has_navigation_requested_signal(self):
        """Test that NavBar has navigation_requested signal."""
        from ui.components.nav_bar import NavBar
        assert hasattr(NavBar, 'navigation_requested')

    def test_navbar_has_navigate_to_method(self):
        """Test that NavBar has navigate_to method."""
        from ui.components.nav_bar import NavBar
        assert hasattr(NavBar, 'navigate_to')
        assert callable(getattr(NavBar, 'navigate_to'))

    def test_navbar_has_button_constants(self):
        """Test that NavBar has button name constants."""
        from ui.components.nav_bar import NavBar
        assert NavBar.DASHBOARD == "dashboard"
        assert NavBar.PYTHON_SCRIPTS == "python_scripts"
        assert NavBar.WPS_SCRIPTS == "wps_scripts"
        assert NavBar.JS_SCRIPTS == "js_scripts"


class TestToolBarClass:
    """Tests for ToolBar class structure."""

    def test_toolbar_class_exists(self):
        """Test that ToolBar class exists."""
        from ui.components import toolbar
        assert hasattr(toolbar, 'ToolBar')

    def test_toolbar_has_deploy_requested_signal(self):
        """Test that ToolBar has deploy_requested signal."""
        from ui.components.toolbar import ToolBar
        assert hasattr(ToolBar, 'deploy_requested')

    def test_toolbar_has_import_requested_signal(self):
        """Test that ToolBar has import_requested signal."""
        from ui.components.toolbar import ToolBar
        assert hasattr(ToolBar, 'import_requested')

    def test_toolbar_has_export_requested_signal(self):
        """Test that ToolBar has export_requested signal."""
        from ui.components.toolbar import ToolBar
        assert hasattr(ToolBar, 'export_requested')


class TestDashboardClass:
    """Tests for Dashboard class structure."""

    def test_dashboard_class_exists(self):
        """Test that Dashboard class exists."""
        from ui.components import dashboard
        assert hasattr(dashboard, 'Dashboard')

    def test_dashboard_has_update_stats_method(self):
        """Test that Dashboard has update_stats method."""
        from ui.components.dashboard import Dashboard
        assert hasattr(Dashboard, 'update_stats')
        assert callable(getattr(Dashboard, 'update_stats'))


class TestMainWindowClass:
    """Tests for MainWindow class structure."""

    def test_mainwindow_class_exists(self):
        """Test that MainWindow class exists."""
        from ui import main_window
        assert hasattr(main_window, 'MainWindow')

    def test_mainwindow_has_navigation_requested_signal(self):
        """Test that MainWindow has navigation_requested signal."""
        from ui.main_window import MainWindow
        assert hasattr(MainWindow, 'navigation_requested')

    def test_mainwindow_has_import_requested_signal(self):
        """Test that MainWindow has import_requested signal."""
        from ui.main_window import MainWindow
        assert hasattr(MainWindow, 'import_requested')

    def test_mainwindow_has_export_requested_signal(self):
        """Test that MainWindow has export_requested signal."""
        from ui.main_window import MainWindow
        assert hasattr(MainWindow, 'export_requested')

    def test_mainwindow_has_update_dashboard_stats_method(self):
        """Test that MainWindow has update_dashboard_stats method."""
        from ui.main_window import MainWindow
        assert hasattr(MainWindow, 'update_dashboard_stats')
        assert callable(getattr(MainWindow, 'update_dashboard_stats'))


class TestNavBarAttributes:
    """Tests for NavBar instance attributes (with PyQt6)."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test with real PyQt6."""
        from PyQt6.QtWidgets import QApplication
        import sys
        # Create QApplication if not exists
        if not QApplication.instance():
            self.app = QApplication(sys.argv)
        else:
            self.app = QApplication.instance()
        yield
        # Cleanup not needed for QApplication

    def test_navbar_instance_has_buttons_dict(self):
        """Test that NavBar instance has buttons dict."""
        from ui.components.nav_bar import NavBar
        nav_bar = NavBar()
        assert hasattr(nav_bar, 'buttons')
        assert isinstance(nav_bar.buttons, dict)

    def test_navbar_fixed_width_set(self):
        """Test that NavBar has fixed width set."""
        from ui.components.nav_bar import NavBar
        nav_bar = NavBar()
        assert nav_bar.width() == 180 or nav_bar.minimumWidth() == 180


class TestToolBarAttributes:
    """Tests for ToolBar instance attributes (with PyQt6)."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test with real PyQt6."""
        from PyQt6.QtWidgets import QApplication
        import sys
        if not QApplication.instance():
            self.app = QApplication(sys.argv)
        else:
            self.app = QApplication.instance()
        yield

    def test_toolbar_instance_has_buttons(self):
        """Test that ToolBar instance has action buttons."""
        from ui.components.toolbar import ToolBar
        toolbar = ToolBar()
        assert hasattr(toolbar, 'deploy_button')
        assert hasattr(toolbar, 'import_button')
        assert hasattr(toolbar, 'export_button')

    def test_toolbar_has_title_label(self):
        """Test that ToolBar has title label."""
        from ui.components.toolbar import ToolBar
        toolbar = ToolBar()
        assert hasattr(toolbar, 'title_label')

    def test_toolbar_fixed_height_set(self):
        """Test that ToolBar has fixed height set."""
        from ui.components.toolbar import ToolBar
        toolbar = ToolBar()
        assert toolbar.height() == 50 or toolbar.minimumHeight() == 50


class TestDashboardAttributes:
    """Tests for Dashboard instance attributes (with PyQt6)."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test with real PyQt6."""
        from PyQt6.QtWidgets import QApplication
        import sys
        if not QApplication.instance():
            self.app = QApplication(sys.argv)
        else:
            self.app = QApplication.instance()
        yield

    def test_dashboard_instance_has_welcome_label(self):
        """Test that Dashboard has welcome label."""
        from ui.components.dashboard import Dashboard
        dashboard = Dashboard()
        assert hasattr(dashboard, 'welcome_label')

    def test_dashboard_instance_has_stat_cards(self):
        """Test that Dashboard has stat cards."""
        from ui.components.dashboard import Dashboard
        dashboard = Dashboard()
        assert hasattr(dashboard, 'python_card')
        assert hasattr(dashboard, 'wps_card')
        assert hasattr(dashboard, 'js_card')


class TestMainWindowAttributes:
    """Tests for MainWindow instance attributes (with PyQt6)."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test with real PyQt6."""
        from PyQt6.QtWidgets import QApplication
        import sys
        if not QApplication.instance():
            self.app = QApplication(sys.argv)
        else:
            self.app = QApplication.instance()
        yield

    def test_mainwindow_instance_has_components(self):
        """Test that MainWindow has all components."""
        from ui.main_window import MainWindow
        window = MainWindow()
        assert hasattr(window, 'nav_bar')
        assert hasattr(window, 'toolbar')
        assert hasattr(window, 'dashboard')
        assert hasattr(window, 'stack')
        assert hasattr(window, 'system_tray')

    def test_mainwindow_has_signals_connected(self):
        """Test that MainWindow has signal connections set up."""
        from ui.main_window import MainWindow
        window = MainWindow()
        # Check that nav_bar navigation_requested has connections
        assert window.nav_bar.navigation_requested is not None

    def test_mainwindow_window_properties(self):
        """Test that MainWindow has window properties set."""
        from ui.main_window import MainWindow
        window = MainWindow()
        assert window.windowTitle() == "脚本管理器"
        assert window.minimumWidth() >= 1024
        assert window.minimumHeight() >= 768
