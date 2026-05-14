"""Tests for SetupWizard class."""

import os
import tempfile
import pytest
from unittest.mock import Mock, patch


@pytest.fixture(autouse=True)
def setup_qapp():
    """Set up QApplication for all tests."""
    from PyQt6.QtWidgets import QApplication
    import sys
    if not QApplication.instance():
        app = QApplication(sys.argv)
    else:
        app = QApplication.instance()
    yield
    # Cleanup not needed for QApplication


@pytest.fixture
def mock_path_detection_service():
    """Create a mock PathDetectionService for testing."""
    service = Mock()
    service.detect_chrome_bookmarks_file.return_value = r"C:\Users\Test\AppData\Local\Google\Chrome\User Data\Default\Bookmarks"
    service.detect_wps_word_startup.return_value = r"C:\Users\Test\AppData\Roaming\Kingsoft\WPS Office\startup\wps"
    service.detect_wps_excel_startup.return_value = r"C:\Users\Test\AppData\Roaming\Kingsoft\WPS Office\startup\et"
    return service


@pytest.fixture
def temp_config_file():
    """Create a temporary config file for testing."""
    fd, path = tempfile.mkstemp(suffix='.json')
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def config_service(temp_config_file):
    """Create a ConfigService instance for testing."""
    from core.config_service import ConfigService
    return ConfigService(temp_config_file)


class TestSetupWizardInit:
    """Test SetupWizard initialization."""

    def test_init_creates_wizard(self, mock_path_detection_service, config_service):
        """Test that SetupWizard can be initialized."""
        from ui.dialogs.setup_wizard import SetupWizard
        wizard = SetupWizard(mock_path_detection_service, config_service)
        assert wizard is not None
        assert wizard.windowTitle() == "首次启动向导 - 配置"

    def test_init_has_three_pages(self, mock_path_detection_service, config_service):
        """Test that SetupWizard has three pages."""
        from ui.dialogs.setup_wizard import SetupWizard
        wizard = SetupWizard(mock_path_detection_service, config_service)
        # Wizard pages are indexed from 0, so 3 pages means IDs 0, 1, 2
        assert wizard.page(0) is not None  # WelcomePage
        assert wizard.page(1) is not None  # PathsPage
        assert wizard.page(2) is not None  # FinishPage

    def test_init_stores_services(self, mock_path_detection_service, config_service):
        """Test that SetupWizard stores the services."""
        from ui.dialogs.setup_wizard import SetupWizard
        wizard = SetupWizard(mock_path_detection_service, config_service)
        assert wizard.path_detection_service is mock_path_detection_service
        assert wizard.config_service is config_service


class TestWelcomePage:
    """Test WelcomePage class."""

    def test_welcome_page_creation(self, mock_path_detection_service, config_service):
        """Test that WelcomePage can be created."""
        from ui.dialogs.setup_wizard import SetupWizard, WelcomePage
        wizard = SetupWizard(mock_path_detection_service, config_service)
        welcome_page = wizard.page(0)
        assert welcome_page is not None
        assert isinstance(welcome_page, WelcomePage)
        assert welcome_page.title() == "欢迎"

    def test_welcome_page_has_next_id(self, mock_path_detection_service, config_service):
        """Test that WelcomePage returns correct next ID."""
        from ui.dialogs.setup_wizard import SetupWizard
        wizard = SetupWizard(mock_path_detection_service, config_service)
        welcome_page = wizard.page(0)
        assert welcome_page.nextId() == 1


class TestPathsPage:
    """Test PathsPage class."""

    def test_paths_page_creation(self, mock_path_detection_service, config_service):
        """Test that PathsPage can be created."""
        from ui.dialogs.setup_wizard import SetupWizard, PathsPage
        wizard = SetupWizard(mock_path_detection_service, config_service)
        paths_page = wizard.page(1)
        assert paths_page is not None
        assert isinstance(paths_page, PathsPage)
        assert paths_page.title() == "路径配置"

    def test_paths_page_auto_detects_paths(self, mock_path_detection_service, config_service):
        """Test that PathsPage auto-detects paths."""
        from ui.dialogs.setup_wizard import SetupWizard
        wizard = SetupWizard(mock_path_detection_service, config_service)
        paths_page = wizard.page(1)

        # Verify auto-detected paths are set
        assert paths_page.chrome_bookmarks_edit.text() == r"C:\Users\Test\AppData\Local\Google\Chrome\User Data\Default\Bookmarks"
        assert paths_page.wps_word_edit.text() == r"C:\Users\Test\AppData\Roaming\Kingsoft\WPS Office\startup\wps"
        assert paths_page.wps_excel_edit.text() == r"C:\Users\Test\AppData\Roaming\Kingsoft\WPS Office\startup\et"

    def test_paths_page_validate_saves_config(self, mock_path_detection_service, config_service, temp_config_file):
        """Test that validatePage saves configuration."""
        from ui.dialogs.setup_wizard import SetupWizard
        wizard = SetupWizard(mock_path_detection_service, config_service)
        paths_page = wizard.page(1)

        # Set custom paths
        paths_page.chrome_bookmarks_edit.setText(r"C:\Custom\Chrome\Bookmarks")
        paths_page.wps_word_edit.setText(r"C:\Custom\WPS\Word")
        paths_page.wps_excel_edit.setText(r"C:\Custom\WPS\Excel")

        # Validate and save
        assert paths_page.validatePage() is True

        # Reload config and verify
        config_service.load()
        assert config_service.get("paths.chrome_bookmarks") == r"C:\Custom\Chrome\Bookmarks"
        assert config_service.get("paths.wps_word_startup") == r"C:\Custom\WPS\Word"
        assert config_service.get("paths.wps_excel_startup") == r"C:\Custom\WPS\Excel"

    def test_paths_page_validate_fails_empty_chrome(self, mock_path_detection_service, config_service):
        """Test that validatePage fails with empty Chrome path."""
        from ui.dialogs.setup_wizard import SetupWizard
        wizard = SetupWizard(mock_path_detection_service, config_service)
        paths_page = wizard.page(1)

        # Clear Chrome path
        paths_page.chrome_bookmarks_edit.setText("")

        # Validate should fail
        assert paths_page.validatePage() is False

    def test_paths_page_validate_fails_empty_word(self, mock_path_detection_service, config_service):
        """Test that validatePage fails with empty Word path."""
        from ui.dialogs.setup_wizard import SetupWizard
        wizard = SetupWizard(mock_path_detection_service, config_service)
        paths_page = wizard.page(1)

        # Clear Word path
        paths_page.wps_word_edit.setText("")

        # Validate should fail
        assert paths_page.validatePage() is False

    def test_paths_page_validate_fails_empty_excel(self, mock_path_detection_service, config_service):
        """Test that validatePage fails with empty Excel path."""
        from ui.dialogs.setup_wizard import SetupWizard
        wizard = SetupWizard(mock_path_detection_service, config_service)
        paths_page = wizard.page(1)

        # Clear Excel path
        paths_page.wps_excel_edit.setText("")

        # Validate should fail
        assert paths_page.validatePage() is False


class TestFinishPage:
    """Test FinishPage class."""

    def test_finish_page_creation(self, mock_path_detection_service, config_service):
        """Test that FinishPage can be created."""
        from ui.dialogs.setup_wizard import SetupWizard, FinishPage
        wizard = SetupWizard(mock_path_detection_service, config_service)
        finish_page = wizard.page(2)
        assert finish_page is not None
        assert isinstance(finish_page, FinishPage)
        assert finish_page.title() == "完成"

    def test_finish_page_is_final(self, mock_path_detection_service, config_service):
        """Test that FinishPage is marked as final."""
        from ui.dialogs.setup_wizard import SetupWizard
        wizard = SetupWizard(mock_path_detection_service, config_service)
        finish_page = wizard.page(2)
        assert finish_page.isFinalPage() is True


class TestSkipFunctionality:
    """Test skip functionality (cancel button)."""

    def test_wizard_has_cancel_button(self, mock_path_detection_service, config_service):
        """Test that wizard has cancel button for skipping."""
        from PyQt6.QtWidgets import QWizard
        from ui.dialogs.setup_wizard import SetupWizard
        wizard = SetupWizard(mock_path_detection_service, config_service)
        # NoCancelButton option should be False, meaning cancel button exists
        assert not wizard.testOption(QWizard.WizardOption.NoCancelButton)

    def test_wizard_can_be_rejected(self, mock_path_detection_service, config_service):
        """Test that wizard can be rejected (skipped)."""
        from ui.dialogs.setup_wizard import SetupWizard
        wizard = SetupWizard(mock_path_detection_service, config_service)
        # Simulate rejection
        wizard.reject()
        # Should not raise any error


class TestPathsPageBrowseButtons:
    """Test browse button functionality."""

    def test_browse_chrome_bookmarks(self, mock_path_detection_service, config_service):
        """Test Chrome bookmarks browse button."""
        from ui.dialogs.setup_wizard import SetupWizard
        wizard = SetupWizard(mock_path_detection_service, config_service)
        paths_page = wizard.page(1)

        # Simulate file selection
        test_path = r"C:\Test\Bookmarks"
        with patch('ui.dialogs.setup_wizard.QFileDialog.getOpenFileName', return_value=(test_path, '')):
            paths_page._browse_chrome_bookmarks()
            assert paths_page.chrome_bookmarks_edit.text() == test_path

    def test_browse_wps_word(self, mock_path_detection_service, config_service):
        """Test WPS Word browse button."""
        from ui.dialogs.setup_wizard import SetupWizard
        wizard = SetupWizard(mock_path_detection_service, config_service)
        paths_page = wizard.page(1)

        # Simulate directory selection
        test_path = r"C:\Test\WPS\Word"
        with patch('ui.dialogs.setup_wizard.QFileDialog.getExistingDirectory', return_value=test_path):
            paths_page._browse_wps_word()
            assert paths_page.wps_word_edit.text() == test_path

    def test_browse_wps_excel(self, mock_path_detection_service, config_service):
        """Test WPS Excel browse button."""
        from ui.dialogs.setup_wizard import SetupWizard
        wizard = SetupWizard(mock_path_detection_service, config_service)
        paths_page = wizard.page(1)

        # Simulate directory selection
        test_path = r"C:\Test\WPS\Excel"
        with patch('ui.dialogs.setup_wizard.QFileDialog.getExistingDirectory', return_value=test_path):
            paths_page._browse_wps_excel()
            assert paths_page.wps_excel_edit.text() == test_path

    def test_browse_cancel_does_not_change_path(self, mock_path_detection_service, config_service):
        """Test that canceling browse dialog doesn't change path."""
        from ui.dialogs.setup_wizard import SetupWizard
        wizard = SetupWizard(mock_path_detection_service, config_service)
        paths_page = wizard.page(1)

        original_chrome = paths_page.chrome_bookmarks_edit.text()

        # Simulate cancel (empty string)
        with patch('ui.dialogs.setup_wizard.QFileDialog.getOpenFileName', return_value=('', '')):
            paths_page._browse_chrome_bookmarks()
            # Path should remain unchanged
            assert paths_page.chrome_bookmarks_edit.text() == original_chrome


class TestPathsPageValidationEdgeCases:
    """Test edge cases for paths page validation."""

    def test_validate_with_whitespace_only_paths(self, mock_path_detection_service, config_service):
        """Test validation fails with whitespace-only paths."""
        from ui.dialogs.setup_wizard import SetupWizard
        wizard = SetupWizard(mock_path_detection_service, config_service)
        paths_page = wizard.page(1)

        # Set whitespace-only paths
        paths_page.chrome_bookmarks_edit.setText("   ")
        paths_page.wps_word_edit.setText("   ")
        paths_page.wps_excel_edit.setText("   ")

        assert paths_page.validatePage() is False

    def test_validate_trims_whitespace(self, mock_path_detection_service, config_service, temp_config_file):
        """Test that validation trims whitespace before saving."""
        from ui.dialogs.setup_wizard import SetupWizard
        wizard = SetupWizard(mock_path_detection_service, config_service)
        paths_page = wizard.page(1)

        # Set paths with leading/trailing whitespace
        paths_page.chrome_bookmarks_edit.setText("  C:\\Test\\Chrome  ")
        paths_page.wps_word_edit.setText("  C:\\Test\\Word  ")
        paths_page.wps_excel_edit.setText("  C:\\Test\\Excel  ")

        assert paths_page.validatePage() is True

        # Verify trimmed paths are saved
        config_service.load()
        assert config_service.get("paths.chrome_bookmarks") == "C:\\Test\\Chrome"
        assert config_service.get("paths.wps_word_startup") == "C:\\Test\\Word"
        assert config_service.get("paths.wps_excel_startup") == "C:\\Test\\Excel"
