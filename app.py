"""Script Manager Application - Main entry point."""

import os
import sys
import platform

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# Import platform utilities
from core.platform_utils import (
    is_bundled, get_bundle_dir, get_app_data_dir,
    ensure_data_dir, copy_default_config
)

# Import services and models
from models.script_model import ScriptModel
from models.repository import Repository
from core.config_service import ConfigService
from core.path_detection_service import PathDetectionService
from core.deployment_service import DeploymentService
from core.import_export_service import ImportExportService
from services.python_service import PythonService
from services.wps_service import WpsService
from services.js_service import JsService
from services.dependency_service import DependencyService
from ui.main_window import MainWindow
from ui.system_tray import SystemTray


def main():
    """Main application entry point.

    This function:
    1. Initializes QApplication
    2. Sets up application paths (handles PyInstaller bundle and cross-platform)
    3. Initializes all services
    4. Shows MainWindow
    5. Runs the application main loop
    """
    # Create QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("脚本管理器")
    app.setOrganizationName("ScriptNexus")

    # Determine base and data directories
    # - base_dir: Read-only resources (templates, icons)
    # - data_dir: Writable user data (config, database)
    if is_bundled():
        # PyInstaller bundled mode
        base_dir = get_bundle_dir()
        data_dir = get_app_data_dir()

        # Ensure data directory exists
        ensure_data_dir()

        # Copy default config if not exists
        copy_default_config()

        # In bundled mode, scripts go in data_dir
        scripts_dir = os.path.join(data_dir, 'scripts')
    else:
        # Development mode
        base_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(base_dir, 'data')

        # In development mode, scripts are in project root
        scripts_dir = os.path.join(base_dir, 'scripts')
    whl_pool_dir = os.path.join(data_dir, 'whl_pool')
    templates_dir = os.path.join(base_dir, 'templates')

    # Ensure writable directories exist
    for directory in [scripts_dir, whl_pool_dir]:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

    # Database and config paths (in writable data_dir)
    db_path = os.path.join(data_dir, 'scripts.db')
    config_path = os.path.join(data_dir, 'config.json')

    # Initialize Repository and ScriptModel
    repository = Repository(db_path)
    script_model = ScriptModel(db_path)
    script_model.create_tables()

    # Initialize ConfigService
    config_service = ConfigService(config_path)
    config_service.load()

    # Initialize PathDetectionService
    path_detection_service = PathDetectionService()

    # Initialize PythonService
    python_service = PythonService(db_path)
    python_service.set_scripts_dir(scripts_dir)

    # Initialize WpsService
    wps_service = WpsService(db_path)
    wps_service.set_paths(
        templates_dir=templates_dir,
        word_startup=config_service.get('paths.wps_word_startup'),
        excel_startup=config_service.get('paths.wps_excel_startup')
    )

    # Initialize JsService
    js_service = JsService(db_path)
    chrome_bookmarks_path = config_service.get('paths.chrome_bookmarks')
    if chrome_bookmarks_path:
        js_service.set_chrome_path(chrome_bookmarks_path)

    # Initialize DependencyService
    dependency_service = DependencyService(whl_pool_dir)
    dependency_service.set_python_service(python_service)

    # Initialize DeploymentService with user-configured template directories
    word_template_dir = config_service.get('paths.wps_word_startup')
    excel_template_dir = config_service.get('paths.wps_excel_startup')
    deployment_service = DeploymentService(wps_service, js_service, word_template_dir, excel_template_dir)

    # Initialize ImportExportService
    import_export_service = ImportExportService(
        scripts_dir=scripts_dir,
        config_path=config_path,
        db_path=db_path,
        templates_dir=templates_dir
    )

    # Show main window
    main_window = MainWindow()
    main_window.set_services(path_detection_service, config_service, deployment_service)
    main_window.import_export_service = import_export_service
    main_window.set_paths(scripts_dir, whl_pool_dir, templates_dir, db_path)
    main_window.show()

    # Keep reference to prevent garbage collection
    app.main_window = main_window

    # Run the application main loop
    sys.exit(app.exec())


if __name__ == '__main__':
    main()