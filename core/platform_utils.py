"""Platform-specific utilities for cross-platform support.

Handles path resolution for Windows and Linux/Kylin systems.
"""
import os
import sys
import platform


# Platform detection
IS_WINDOWS = platform.system() == 'Windows'
IS_LINUX = platform.system() == 'Linux'
IS_MACOS = platform.system() == 'Darwin'

# Kylin system detection (Chinese Linux distribution)
IS_KYLIN = IS_LINUX and (
    os.path.exists('/etc/kylin-release') or
    'kylin' in platform.platform().lower()
)


def is_bundled():
    """Check if running in PyInstaller bundled mode.

    Returns:
        True if bundled, False if running from source
    """
    return hasattr(sys, '_MEIPASS')


def get_bundle_dir():
    """Get the bundle directory (read-only resources).

    Returns:
        Path to the bundle directory
    """
    if is_bundled():
        return sys._MEIPASS
    else:
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_app_data_dir():
    """Get writable application data directory based on platform.

    Config files, database, and user data should be stored here.

    Returns:
        Path to writable data directory
    """
    if is_bundled():
        # Bundled mode: use platform-specific data dir
        if IS_WINDOWS:
            app_data = os.environ.get('APPDATA', '')
            if app_data:
                return os.path.join(app_data, 'ScriptNexus')
            else:
                return os.path.join(os.path.expanduser('~'), 'ScriptNexus')
        elif IS_LINUX:
            # Linux/Kylin: Use XDG standard
            xdg_data_home = os.environ.get('XDG_DATA_HOME', '')
            if xdg_data_home:
                return os.path.join(xdg_data_home, 'scriptnexus')
            else:
                return os.path.join(os.path.expanduser('~'), '.local', 'share', 'scriptnexus')
        elif IS_MACOS:
            return os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', 'ScriptNexus')
        else:
            return os.path.join(os.path.expanduser('~'), 'ScriptNexus')
    else:
        # Development mode: use project data directory
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(project_dir, 'data')


def get_config_path():
    """Get configuration file path.

    Returns:
        Path to config.json
    """
    return os.path.join(get_app_data_dir(), 'data', 'config.json')


def get_db_path():
    """Get database file path.

    Returns:
        Path to scripts.db
    """
    return os.path.join(get_app_data_dir(), 'scripts.db')


def get_resource_path(relative_path):
    """Get absolute path to bundled resource.

    Args:
        relative_path: Path relative to bundle root

    Returns:
        Absolute path to the resource
    """
    return os.path.join(get_bundle_dir(), relative_path)


def ensure_data_dir():
    """Ensure the data directory exists.

    Creates the directory if it doesn't exist.
    """
    data_dir = get_app_data_dir()
    if not os.path.exists(data_dir):
        try:
            os.makedirs(data_dir, exist_ok=True)
        except Exception as e:
            print(f"Warning: Could not create data directory: {e}")
    return data_dir


def copy_default_config():
    """Copy default config to data directory if not exists.

    Returns:
        True if copied, False if already exists or failed
    """
    config_path = get_config_path()
    if os.path.exists(config_path):
        return False

    # Get default config from bundle
    default_config = get_resource_path('data/config.json')
    if os.path.exists(default_config):
        try:
            import shutil
            ensure_data_dir()
            # Ensure data subdir exists
            data_subdir = os.path.dirname(config_path)
            if not os.path.exists(data_subdir):
                os.makedirs(data_subdir, exist_ok=True)
            shutil.copy(default_config, config_path)
            return True
        except Exception as e:
            print(f"Warning: Could not copy default config: {e}")
            return False
    return False


def get_wps_user_data_dir():
    """Get WPS user data directory based on platform.

    Returns:
        Path to WPS configuration directory
    """
    if IS_WINDOWS:
        return os.path.join(os.environ.get('APPDATA', ''), 'Kingsoft', 'office6')
    elif IS_LINUX:
        # WPS on Linux
        return os.path.join(os.path.expanduser('~'), '.kingsoft', 'office6')
    else:
        return None


def get_chrome_bookmarks_path():
    """Get Chrome bookmarks file path based on platform.

    Returns:
        Path to Chrome bookmarks file
    """
    if IS_WINDOWS:
        return os.path.join(
            os.environ.get('LOCALAPPDATA', ''),
            'Google', 'Chrome', 'User Data', 'Default', 'Bookmarks'
        )
    elif IS_LINUX:
        return os.path.join(
            os.path.expanduser('~'),
            '.config', 'google-chrome', 'Default', 'Bookmarks'
        )
    else:
        return None