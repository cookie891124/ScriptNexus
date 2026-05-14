"""Tests for PathDetectionService class."""

import os
import pytest
from unittest.mock import patch

from core.path_detection_service import PathDetectionService


@pytest.fixture
def service():
    """Create a PathDetectionService instance for testing."""
    return PathDetectionService()


class TestPathDetectionService:
    """Test cases for PathDetectionService class."""

    def test_detect_chrome_user_data_default(self, service):
        """Test detect_chrome_user_data returns default path when not exists."""
        with patch.object(service, '_path_exists', return_value=False):
            result = service.detect_chrome_user_data()
            assert 'AppData' in result or 'Chrome' in result

    def test_detect_chrome_user_data_custom(self, service):
        """Test detect_chrome_user_data returns path when exists."""
        with patch.object(service, '_path_exists', return_value=True):
            result = service.detect_chrome_user_data()
            assert result is not None
            assert len(result) > 0

    def test_detect_chrome_bookmarks_file_default(self, service):
        """Test detect_chrome_bookmarks_file returns default path when not exists."""
        with patch.object(service, '_path_exists', return_value=False):
            result = service.detect_chrome_bookmarks_file()
            assert 'Bookmarks' in result

    def test_detect_chrome_bookmarks_file_custom(self, service):
        """Test detect_chrome_bookmarks_file returns path when exists."""
        with patch.object(service, '_path_exists', return_value=True):
            result = service.detect_chrome_bookmarks_file()
            assert result is not None
            assert len(result) > 0

    def test_detect_wps_word_startup_default(self, service):
        """Test detect_wps_word_startup returns default path."""
        result = service.detect_wps_word_startup()
        assert 'startup' in result.lower() or 'StartUp' in result

    def test_detect_wps_excel_startup_default(self, service):
        """Test detect_wps_excel_startup returns default path."""
        result = service.detect_wps_excel_startup()
        assert 'startup' in result.lower() or 'StartUp' in result

    def test_detect_wps_installation_default(self, service):
        """Test detect_wps_installation returns default path when not exists."""
        with patch.object(service, '_path_exists', return_value=False):
            result = service.detect_wps_installation()
            assert 'WPS' in result or 'Kingsoft' in result

    def test_detect_wps_installation_custom(self, service):
        """Test detect_wps_installation returns path when exists."""
        with patch.object(service, '_path_exists', return_value=True):
            result = service.detect_wps_installation()
            assert result is not None
            assert len(result) > 0

    def test_get_default_scripts_dir(self, service):
        """Test get_default_scripts_dir returns valid path."""
        result = service.get_default_scripts_dir()
        assert result is not None
        assert len(result) > 0

    def test_get_default_whl_pool_dir(self, service):
        """Test get_default_whl_pool_dir returns valid path."""
        result = service.get_default_whl_pool_dir()
        assert result is not None
        assert len(result) > 0

    def test_get_default_config_dir(self, service):
        """Test get_default_config_dir returns valid path."""
        result = service.get_default_config_dir()
        assert result is not None
        assert len(result) > 0

    def test_paths_use_user_profile(self, service):
        """Test that default paths use USERPROFILE environment variable."""
        with patch.dict(os.environ, {'USERPROFILE': r'C:\TestUser'}):
            scripts_dir = service.get_default_scripts_dir()
            whl_pool_dir = service.get_default_whl_pool_dir()

            assert 'C:\\TestUser' in scripts_dir or scripts_dir.startswith('C:\\TestUser')
            assert 'C:\\TestUser' in whl_pool_dir or whl_pool_dir.startswith('C:\\TestUser')

    def test_paths_use_appdata(self, service):
        """Test that some paths use APPDATA environment variable."""
        with patch.dict(os.environ, {'APPDATA': r'C:\TestAppData'}):
            config_dir = service.get_default_config_dir()
            assert 'C:\\TestAppData' in config_dir or config_dir.startswith('C:\\TestAppData')


class TestPathDetectionServiceIntegration:
    """Integration tests for PathDetectionService with real environment."""

    def test_detect_chrome_user_data_integration(self):
        """Test detect_chrome_user_data with real environment."""
        service = PathDetectionService()
        result = service.detect_chrome_user_data()
        assert result is not None
        assert len(result) > 0

    def test_detect_chrome_bookmarks_file_integration(self):
        """Test detect_chrome_bookmarks_file with real environment."""
        service = PathDetectionService()
        result = service.detect_chrome_bookmarks_file()
        assert result is not None
        assert len(result) > 0

    def test_detect_wps_word_startup_integration(self):
        """Test detect_wps_word_startup with real environment."""
        service = PathDetectionService()
        result = service.detect_wps_word_startup()
        assert result is not None
        assert len(result) > 0

    def test_detect_wps_excel_startup_integration(self):
        """Test detect_wps_excel_startup with real environment."""
        service = PathDetectionService()
        result = service.detect_wps_excel_startup()
        assert result is not None
        assert len(result) > 0

    def test_detect_wps_installation_integration(self):
        """Test detect_wps_installation with real environment."""
        service = PathDetectionService()
        result = service.detect_wps_installation()
        assert result is not None
        assert len(result) > 0

    def test_get_default_scripts_dir_integration(self):
        """Test get_default_scripts_dir with real environment."""
        service = PathDetectionService()
        result = service.get_default_scripts_dir()
        assert result is not None
        assert len(result) > 0

    def test_get_default_whl_pool_dir_integration(self):
        """Test get_default_whl_pool_dir with real environment."""
        service = PathDetectionService()
        result = service.get_default_whl_pool_dir()
        assert result is not None
        assert len(result) > 0

    def test_get_default_config_dir_integration(self):
        """Test get_default_config_dir with real environment."""
        service = PathDetectionService()
        result = service.get_default_config_dir()
        assert result is not None
        assert len(result) > 0
