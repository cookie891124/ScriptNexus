"""Tests for SystemTray class."""

import pytest
from unittest.mock import MagicMock, patch


# Mock PyQt6 modules before importing SystemTray
@pytest.fixture(autouse=True)
def mock_pyqt6():
    """Mock all PyQt6 imports used in system_tray module."""
    with patch('ui.system_tray.QSystemTrayIcon') as mock_tray, \
         patch('ui.system_tray.QMenu') as mock_menu, \
         patch('ui.system_tray.QAction') as mock_action, \
         patch('ui.system_tray.QIcon') as mock_icon:

        # Setup MessageIcon enum mock
        mock_msg_icon = MagicMock()
        mock_tray.MessageIcon = mock_msg_icon
        mock_msg_icon.Information = 0
        mock_msg_icon.Warning = 1
        mock_msg_icon.Critical = 2
        mock_msg_icon.NoIcon = 3

        # Setup ActivationReason enum mock
        mock_reason = MagicMock()
        mock_tray.ActivationReason = mock_reason
        mock_reason.DoubleClick = 2
        mock_reason.Trigger = 1
        mock_reason.Context = 0
        mock_reason.MiddleClick = 3

        yield {
            'tray': mock_tray,
            'menu': mock_menu,
            'action': mock_action,
            'icon': mock_icon
        }


@pytest.fixture
def mock_app():
    """Create a mock QApplication instance for testing."""
    return MagicMock()


class TestSystemTrayInit:
    """Test SystemTray initialization."""

    def test_init_creates_tray_icon(self, mock_app, mock_pyqt6):
        """Test that __init__ creates QSystemTrayIcon instance."""
        from ui.system_tray import SystemTray
        tray = SystemTray(mock_app)
        mock_pyqt6['tray'].assert_called_once()

    def test_init_calls_setup_icon(self, mock_app, mock_pyqt6):
        """Test that __init__ results in icon setup."""
        from ui.system_tray import SystemTray
        tray = SystemTray(mock_app)
        # Verify icon was set up (setIcon was called)
        mock_pyqt6['tray'].return_value.setIcon.assert_called()

    def test_init_calls_setup_menu(self, mock_app, mock_pyqt6):
        """Test that __init__ results in menu setup."""
        from ui.system_tray import SystemTray
        tray = SystemTray(mock_app)
        # Verify menu was set up (setContextMenu was called)
        mock_pyqt6['tray'].return_value.setContextMenu.assert_called()

    def test_init_stores_tray_icon(self, mock_app, mock_pyqt6):
        """Test that __init__ stores the tray icon instance."""
        from ui.system_tray import SystemTray
        tray = SystemTray(mock_app)
        assert tray.tray_icon is not None


class TestSetupIcon:
    """Test _setup_icon method."""

    def test_setup_icon_sets_icon(self, mock_app, mock_pyqt6):
        """Test that _setup_icon sets the tray icon."""
        from ui.system_tray import SystemTray
        tray = SystemTray(mock_app)

        # Verify setIcon was called (icon may be from QApplication.style().standardIcon)
        mock_pyqt6['tray'].return_value.setIcon.assert_called()

    def test_setup_icon_calls_set_visible(self, mock_app, mock_pyqt6):
        """Test that _setup_icon calls setVisible(True) on the tray icon."""
        from ui.system_tray import SystemTray
        tray = SystemTray(mock_app)
        # Verify setVisible(True) was called instead of show()
        mock_pyqt6['tray'].return_value.setVisible.assert_called_with(True)


class TestSetupMenu:
    """Test _setup_menu method."""

    def test_setup_menu_creates_menu(self, mock_app, mock_pyqt6):
        """Test that _setup_menu creates a QMenu."""
        from ui.system_tray import SystemTray
        tray = SystemTray(mock_app)
        mock_pyqt6['menu'].assert_called_once()

    def test_setup_menu_sets_menu_to_tray(self, mock_app, mock_pyqt6):
        """Test that _setup_menu sets the menu to the tray icon."""
        from ui.system_tray import SystemTray
        tray = SystemTray(mock_app)
        mock_pyqt6['tray'].return_value.setContextMenu.assert_called_once()

    def test_setup_menu_creates_three_actions(self, mock_app, mock_pyqt6):
        """Test that _setup_menu creates 3 actions (open, deploy, quit)."""
        from ui.system_tray import SystemTray
        tray = SystemTray(mock_app)
        # Check that 3 actions are created
        assert mock_pyqt6['action'].call_count == 3

    def test_setup_menu_adds_separator(self, mock_app, mock_pyqt6):
        """Test that _setup_menu adds a separator before quit."""
        from ui.system_tray import SystemTray
        tray = SystemTray(mock_app)
        menu_instance = mock_pyqt6['menu'].return_value
        menu_instance.addSeparator.assert_called_once()

    def test_setup_menu_connects_open_action(self, mock_app, mock_pyqt6):
        """Test that open action is created and stored."""
        from ui.system_tray import SystemTray
        tray = SystemTray(mock_app)

        # Verify open_action exists
        assert tray.open_action is not None


class TestOnActivated:
    """Test _on_activated method."""

    def test_on_activated_emits_show_main_window_on_doubleclick(self, mock_app, mock_pyqt6):
        """Test that _on_activated emits show_main_window on double-click."""
        from ui.system_tray import SystemTray
        tray = SystemTray(mock_app)

        # Connect to signal
        callback = MagicMock()
        tray.show_main_window.connect(callback)

        # Simulate double-click (reason=2)
        tray._on_activated(2)  # DoubleClick

        callback.assert_called_once()

    def test_on_activated_nothing_on_trigger(self, mock_app, mock_pyqt6):
        """Test that _on_activated does nothing on single trigger."""
        from ui.system_tray import SystemTray
        tray = SystemTray(mock_app)

        callback = MagicMock()
        tray.show_main_window.connect(callback)

        # Simulate trigger (reason=1)
        tray._on_activated(1)  # Trigger

        callback.assert_not_called()


class TestShowMessage:
    """Test show_message method."""

    def test_show_message_calls_tray_show_message(self, mock_app, mock_pyqt6):
        """Test that show_message calls the tray icon's showMessage."""
        from ui.system_tray import SystemTray
        tray = SystemTray(mock_app)
        tray.show_message("Title", "Message", "Information", 5000)

        tray.tray_icon.showMessage.assert_called_once_with(
            "Title", "Message",
            0,  # Information icon value
            5000
        )

    def test_show_message_default_msecs(self, mock_app, mock_pyqt6):
        """Test that show_message uses default msecs."""
        from ui.system_tray import SystemTray
        tray = SystemTray(mock_app)
        tray.show_message("Title", "Message", "Information")

        tray.tray_icon.showMessage.assert_called_once()

    def test_show_message_warning_icon(self, mock_app, mock_pyqt6):
        """Test show_message with Warning icon."""
        from ui.system_tray import SystemTray
        tray = SystemTray(mock_app)
        tray.show_message("Title", "Message", "Warning", 3000)

        tray.tray_icon.showMessage.assert_called_once_with(
            "Title", "Message",
            1,  # Warning icon value
            3000
        )

    def test_show_message_critical_icon(self, mock_app, mock_pyqt6):
        """Test show_message with Critical icon."""
        from ui.system_tray import SystemTray
        tray = SystemTray(mock_app)
        tray.show_message("Title", "Message", "Critical", 5000)

        tray.tray_icon.showMessage.assert_called_once_with(
            "Title", "Message",
            2,  # Critical icon value
            5000
        )


class TestSignals:
    """Test SystemTray signals."""

    def test_show_main_window_signal_exists(self, mock_app, mock_pyqt6):
        """Test that show_main_window signal exists."""
        from ui.system_tray import SystemTray
        tray = SystemTray(mock_app)
        assert hasattr(tray, 'show_main_window')

    def test_deploy_triggered_signal_exists(self, mock_app, mock_pyqt6):
        """Test that deploy_triggered signal exists."""
        from ui.system_tray import SystemTray
        tray = SystemTray(mock_app)
        assert hasattr(tray, 'deploy_triggered')

    def test_quit_triggered_signal_exists(self, mock_app, mock_pyqt6):
        """Test that quit_triggered signal exists."""
        from ui.system_tray import SystemTray
        tray = SystemTray(mock_app)
        assert hasattr(tray, 'quit_triggered')

    def test_signals_are_pyqt_signals(self, mock_app, mock_pyqt6):
        """Test that signals are proper pyqtSignal instances."""
        from ui.system_tray import SystemTray
        tray = SystemTray(mock_app)

        # Signals should be callable (emit method)
        assert hasattr(tray.show_main_window, 'connect')
        assert hasattr(tray.deploy_triggered, 'connect')
        assert hasattr(tray.quit_triggered, 'connect')


class TestSystemTrayIntegration:
    """Integration tests for SystemTray."""

    def test_full_initialization(self, mock_app, mock_pyqt6):
        """Test full initialization of SystemTray."""
        from ui.system_tray import SystemTray
        tray = SystemTray(mock_app)

        # Verify all components are initialized
        assert tray.tray_icon is not None
        assert hasattr(tray, 'show_main_window')
        assert hasattr(tray, 'deploy_triggered')
        assert hasattr(tray, 'quit_triggered')

        # Verify tray_icon methods were called
        mock_pyqt6['tray'].return_value.setVisible.assert_called_with(True)
        mock_pyqt6['tray'].return_value.setContextMenu.assert_called()

    def test_action_callbacks_connected(self, mock_app, mock_pyqt6):
        """Test that all action callbacks are properly connected."""
        from ui.system_tray import SystemTray
        tray = SystemTray(mock_app)

        # Verify actions exist
        assert tray.open_action is not None
        assert tray.deploy_action is not None
        assert tray.quit_action is not None
