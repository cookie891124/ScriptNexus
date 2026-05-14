"""Runtime hook for PyInstaller packaged application.

Handles path resolution for bundled resources and cross-platform support.
"""
import os
import sys
import platform


def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and PyInstaller.

    Args:
        relative_path: Path relative to the application root

    Returns:
        Absolute path to the resource
    """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller creates a temp folder in _MEIPASS
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


def get_app_data_dir():
    """Get writable application data directory based on platform.

    Returns:
        Path to writable data directory for config/database
    """
    if platform.system() == 'Windows':
        # Windows: Use AppData
        app_data = os.environ.get('APPDATA', '')
        if app_data:
            return os.path.join(app_data, 'ScriptNexus')
        else:
            # Fallback to user home
            return os.path.join(os.path.expanduser('~'), 'ScriptNexus')
    else:
        # Linux/Kylin: Use XDG standard
        xdg_data_home = os.environ.get('XDG_DATA_HOME', '')
        if xdg_data_home:
            return os.path.join(xdg_data_home, 'scriptnexus')
        else:
            return os.path.join(os.path.expanduser('~'), '.local', 'share', 'scriptnexus')


# Set environment variables for bundled mode
if hasattr(sys, '_MEIPASS'):
    os.environ['WPS_ADDONS_BUNDLED'] = 'true'
    os.environ['WPS_ADDONS_RESOURCE_BASE'] = sys._MEIPASS
    os.environ['WPS_ADDONS_DATA_DIR'] = get_app_data_dir()

    # Ensure data directory exists
    data_dir = get_app_data_dir()
    if not os.path.exists(data_dir):
        try:
            os.makedirs(data_dir, exist_ok=True)
        except Exception:
            pass