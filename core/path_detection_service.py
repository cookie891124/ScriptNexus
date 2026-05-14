"""PathDetectionService for auto-detecting Chrome and WPS installation paths."""

import os
from typing import Optional


class PathDetectionService:
    """Service for detecting Chrome and WPS installation paths and directories."""

    def __init__(self):
        """Initialize PathDetectionService."""
        pass

    def _get_chrome_user_data_path(self) -> str:
        """Get the default Chrome user data path.

        Returns:
            Path to Chrome user data directory.
        """
        return os.path.join(
            os.environ.get('LOCALAPPDATA', ''),
            'Google', 'Chrome', 'User Data'
        )

    def _get_chrome_bookmarks_path(self) -> str:
        """Get the default Chrome bookmarks file path.

        Returns:
            Path to Chrome bookmarks file.
        """
        return os.path.join(
            os.environ.get('LOCALAPPDATA', ''),
            'Google', 'Chrome', 'User Data', 'Default', 'Bookmarks'
        )

    def _get_wps_word_startup_path(self) -> str:
        """Get the default WPS Word startup path.

        Returns:
            Path to WPS Word startup directory.
        """
        return os.path.join(
            os.environ.get('APPDATA', ''),
            'Kingsoft', 'WPS Office', 'startup', 'wps'
        )

    def _get_wps_excel_startup_path(self) -> str:
        """Get the default WPS Excel startup path.

        Returns:
            Path to WPS Excel startup directory.
        """
        return os.path.join(
            os.environ.get('APPDATA', ''),
            'Kingsoft', 'WPS Office', 'startup', 'et'
        )

    def _get_wps_installation_path(self) -> str:
        """Get the default WPS installation path.

        Returns:
            Path to WPS installation directory.
        """
        return os.path.join(
            os.environ.get('ProgramFiles', 'C:\\Program Files'),
            'WPS Office'
        )

    def _path_exists(self, path: str) -> bool:
        """Check if a path exists.

        Args:
            path: The path to check.

        Returns:
            True if path exists, False otherwise.
        """
        return os.path.exists(path)

    def detect_chrome_user_data(self) -> str:
        """Detect Chrome user data directory.

        Returns:
            Path to Chrome user data directory, or default path if not found.
        """
        default_path = self._get_chrome_user_data_path()
        if self._path_exists(default_path):
            return default_path
        return default_path

    def detect_chrome_bookmarks_file(self) -> str:
        """Detect Chrome bookmarks file path.

        Returns:
            Path to Chrome bookmarks file, or default path if not found.
        """
        default_path = self._get_chrome_bookmarks_path()
        if self._path_exists(default_path):
            return default_path
        return default_path

    def detect_wps_word_startup(self) -> str:
        """Detect WPS Word startup directory.

        Returns:
            Path to WPS Word startup directory.
        """
        return self._get_wps_word_startup_path()

    def detect_wps_excel_startup(self) -> str:
        """Detect WPS Excel startup directory.

        Returns:
            Path to WPS Excel startup directory.
        """
        return self._get_wps_excel_startup_path()

    def detect_wps_installation(self) -> str:
        """Detect WPS installation directory.

        Returns:
            Path to WPS installation directory, or default path if not found.
        """
        default_path = self._get_wps_installation_path()
        if self._path_exists(default_path):
            return default_path
        return default_path

    def get_default_scripts_dir(self) -> str:
        """Get default scripts directory.

        Returns:
            Path to default scripts directory.
        """
        return os.path.join(
            os.environ.get('USERPROFILE', ''),
            'ScriptNexus', 'scripts'
        )

    def get_default_whl_pool_dir(self) -> str:
        """Get default whl file pool directory.

        Returns:
            Path to default whl pool directory.
        """
        return os.path.join(
            os.environ.get('USERPROFILE', ''),
            'ScriptNexus', 'whl_pool'
        )

    def get_default_config_dir(self) -> str:
        """Get default configuration directory.

        Returns:
            Path to default configuration directory.
        """
        return os.path.join(
            os.environ.get('APPDATA', ''),
            'ScriptNexus', 'config'
        )
