"""Tests for ImportExportService class."""

import json
import os
import shutil
import sqlite3
import tempfile
import pytest

from core.import_export_service import ImportExportService


@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing."""
    base_dir = tempfile.mkdtemp()

    scripts_dir = os.path.join(base_dir, 'scripts')
    os.makedirs(scripts_dir)

    templates_dir = os.path.join(base_dir, 'templates')
    os.makedirs(templates_dir)

    data_dir = os.path.join(base_dir, 'data')
    os.makedirs(data_dir)

    config_path = os.path.join(data_dir, 'config.json')
    db_path = os.path.join(data_dir, 'scripts.db')

    yield {
        'base_dir': base_dir,
        'scripts_dir': scripts_dir,
        'templates_dir': templates_dir,
        'config_path': config_path,
        'db_path': db_path
    }

    shutil.rmtree(base_dir, ignore_errors=True)


@pytest.fixture
def import_export_service(temp_dirs):
    """Create an ImportExportService instance for testing."""
    # Create initial config file
    with open(temp_dirs['config_path'], 'w', encoding='utf-8') as f:
        json.dump({'app_name': 'WPS Script Manager', 'version': '1.0.0'}, f)

    # Create initial database
    conn = sqlite3.connect(temp_dirs['db_path'])
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scripts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            content TEXT,
            target_app TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute("INSERT INTO scripts (name, content, target_app) VALUES ('TestScript', 'print(1)', 'python')")
    conn.commit()
    conn.close()

    return ImportExportService(
        scripts_dir=temp_dirs['scripts_dir'],
        config_path=temp_dirs['config_path'],
        db_path=temp_dirs['db_path'],
        templates_dir=temp_dirs['templates_dir']
    )


class TestImportExportServiceInit:
    """Test ImportExportService initialization."""

    def test_init_with_valid_paths(self, temp_dirs):
        """Test initialization with valid paths."""
        service = ImportExportService(
            scripts_dir=temp_dirs['scripts_dir'],
            config_path=temp_dirs['config_path'],
            db_path=temp_dirs['db_path'],
            templates_dir=temp_dirs['templates_dir']
        )
        assert service.scripts_dir == temp_dirs['scripts_dir']
        assert service.config_path == temp_dirs['config_path']
        assert service.db_path == temp_dirs['db_path']
        assert service.templates_dir == temp_dirs['templates_dir']


class TestExportAll:
    """Test export_all method."""

    def test_export_empty_directories(self, import_export_service, temp_dirs):
        """Test export with empty directories."""
        result = import_export_service.export_all()

        assert result['success'] is True
        assert result['zip_path'] is not None
        assert result['error'] is None
        assert os.path.exists(result['zip_path'])
        assert 'scripts_backup_' in result['zip_path']
        assert result['zip_path'].endswith('.zip')

    def test_export_with_scripts(self, import_export_service, temp_dirs):
        """Test export with scripts in scripts directory."""
        # Create a script file
        script_file = os.path.join(temp_dirs['scripts_dir'], 'test_script.py')
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write('print("Hello World")')

        result = import_export_service.export_all()

        assert result['success'] is True
        assert os.path.exists(result['zip_path'])

        # Verify ZIP contents
        import zipfile
        with zipfile.ZipFile(result['zip_path'], 'r') as zipf:
            names = zipf.namelist()
            assert any('scripts/test_script.py' in name for name in names)

    def test_export_with_templates(self, import_export_service, temp_dirs):
        """Test export with templates in templates directory."""
        # Create a template file
        template_file = os.path.join(temp_dirs['templates_dir'], 'template.dotm')
        with open(template_file, 'w', encoding='utf-8') as f:
            f.write('Template content')

        result = import_export_service.export_all()

        assert result['success'] is True
        assert os.path.exists(result['zip_path'])

        # Verify ZIP contents
        import zipfile
        with zipfile.ZipFile(result['zip_path'], 'r') as zipf:
            names = zipf.namelist()
            assert any('templates/template.dotm' in name for name in names)

    def test_export_with_nested_scripts(self, import_export_service, temp_dirs):
        """Test export with nested script directories."""
        # Create nested directory structure
        nested_dir = os.path.join(temp_dirs['scripts_dir'], 'python', 'utils')
        os.makedirs(nested_dir)
        nested_file = os.path.join(nested_dir, 'helper.py')
        with open(nested_file, 'w', encoding='utf-8') as f:
            f.write('def helper(): pass')

        result = import_export_service.export_all()

        assert result['success'] is True
        assert os.path.exists(result['zip_path'])

        # Verify ZIP contents
        import zipfile
        with zipfile.ZipFile(result['zip_path'], 'r') as zipf:
            names = zipf.namelist()
            assert any('python/utils/helper.py' in name for name in names)


class TestImportPackage:
    """Test import_package method."""

    def test_import_invalid_zip(self, import_export_service):
        """Test import with non-existent file."""
        result = import_export_service.import_package('/non/existent/path.zip')

        assert result['success'] is False
        assert result['error'] is not None
        assert 'not found' in result['error'].lower()

    def test_import_not_zip_file(self, temp_dirs):
        """Test import with a non-ZIP file."""
        # Create a text file with .zip extension
        fake_zip = os.path.join(temp_dirs['base_dir'], 'fake.zip')
        with open(fake_zip, 'w') as f:
            f.write('This is not a zip file')

        service = ImportExportService(
            scripts_dir=temp_dirs['scripts_dir'],
            config_path=temp_dirs['config_path'],
            db_path=temp_dirs['db_path'],
            templates_dir=temp_dirs['templates_dir']
        )

        result = service.import_package(fake_zip)

        assert result['success'] is False
        assert result['error'] is not None

    def test_import_merge_mode(self, import_export_service, temp_dirs):
        """Test import in merge mode."""
        # First, create a backup
        export_result = import_export_service.export_all()
        assert export_result['success'] is True

        # Modify existing config
        with open(temp_dirs['config_path'], 'w', encoding='utf-8') as f:
            json.dump({'app_name': 'Modified', 'new_key': 'new_value'}, f)

        # Import the backup in merge mode
        result = import_export_service.import_package(export_result['zip_path'], merge=True)

        assert result['success'] is True
        assert result['error'] is None

        # Verify config was merged (should have both old and new keys)
        with open(temp_dirs['config_path'], 'r', encoding='utf-8') as f:
            config = json.load(f)
        assert 'app_name' in config
        assert 'version' in config
        assert 'new_key' in config

    def test_import_overwrite_mode(self, import_export_service, temp_dirs):
        """Test import in overwrite mode."""
        # First, create a backup
        export_result = import_export_service.export_all()
        assert export_result['success'] is True

        # Modify existing config
        with open(temp_dirs['config_path'], 'w', encoding='utf-8') as f:
            json.dump({'app_name': 'Modified', 'new_key': 'new_value'}, f)

        # Import the backup in overwrite mode
        result = import_export_service.import_package(export_result['zip_path'], merge=False)

        assert result['success'] is True
        assert result['error'] is None

        # Verify config was overwritten (should only have original keys)
        with open(temp_dirs['config_path'], 'r', encoding='utf-8') as f:
            config = json.load(f)
        assert 'app_name' in config
        assert 'version' in config
        assert 'new_key' not in config

    def test_import_with_scripts(self, import_export_service, temp_dirs):
        """Test import with script files."""
        # Create a script file
        script_file = os.path.join(temp_dirs['scripts_dir'], 'import_test.py')
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write('print("Import test")')

        # Export
        export_result = import_export_service.export_all()
        assert export_result['success'] is True

        # Remove the script
        os.remove(script_file)

        # Import
        result = import_export_service.import_package(export_result['zip_path'], merge=True)

        assert result['success'] is True
        assert os.path.exists(script_file)

    def test_import_with_templates(self, import_export_service, temp_dirs):
        """Test import with template files."""
        # Create a template file
        template_file = os.path.join(temp_dirs['templates_dir'], 'import_test.dotm')
        with open(template_file, 'w', encoding='utf-8') as f:
            f.write('Import test template')

        # Export
        export_result = import_export_service.export_all()
        assert export_result['success'] is True

        # Remove the template
        os.remove(template_file)

        # Import
        result = import_export_service.import_package(export_result['zip_path'], merge=True)

        assert result['success'] is True
        assert os.path.exists(template_file)


class TestValidateStructure:
    """Test _validate_structure method."""

    def test_validate_valid_package(self, import_export_service, temp_dirs):
        """Test validation of a valid package."""
        # Create a valid package structure
        package_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(package_dir, 'scripts'))
        with open(os.path.join(package_dir, 'config.json'), 'w') as f:
            json.dump({'test': 'config'}, f)

        result = import_export_service._validate_structure(package_dir)

        assert result['valid'] is True
        assert result['error'] is None
        assert 'scripts/' in result['found_files']
        assert 'config.json' in result['found_files']

        shutil.rmtree(package_dir, ignore_errors=True)

    def test_validate_package_with_db_only(self, import_export_service, temp_dirs):
        """Test validation of package with only database."""
        package_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(package_dir, 'scripts'))

        # Create database only (no config.json)
        conn = sqlite3.connect(os.path.join(package_dir, 'scripts.db'))
        conn.close()

        result = import_export_service._validate_structure(package_dir)

        assert result['valid'] is True
        assert result['error'] is None

        shutil.rmtree(package_dir, ignore_errors=True)

    def test_validate_invalid_package(self, import_export_service):
        """Test validation of an invalid package."""
        package_dir = tempfile.mkdtemp()
        # No scripts, config, or db

        result = import_export_service._validate_structure(package_dir)

        assert result['valid'] is False
        assert result['error'] is not None
        assert 'missing' in result['error'].lower()

        shutil.rmtree(package_dir, ignore_errors=True)

    def test_validate_empty_directory(self, import_export_service):
        """Test validation of an empty directory."""
        package_dir = tempfile.mkdtemp()

        result = import_export_service._validate_structure(package_dir)

        assert result['valid'] is False
        assert result['error'] is not None

        shutil.rmtree(package_dir, ignore_errors=True)


class TestMergeImport:
    """Test _merge_import method."""

    def test_merge_scripts_directory(self, import_export_service, temp_dirs):
        """Test merging scripts directory."""
        # Create source directory with scripts
        source_dir = tempfile.mkdtemp()
        source_scripts = os.path.join(source_dir, 'scripts')
        os.makedirs(source_scripts)

        # Create a script in source
        with open(os.path.join(source_scripts, 'merged_script.py'), 'w') as f:
            f.write('print("Merged")')

        result = import_export_service._merge_import(source_dir)

        assert result['success'] is True
        assert os.path.exists(os.path.join(temp_dirs['scripts_dir'], 'merged_script.py'))

        shutil.rmtree(source_dir, ignore_errors=True)

    def test_merge_config_deep_merge(self, import_export_service, temp_dirs):
        """Test deep merge of configuration."""
        # Set up existing config with nested structure
        with open(temp_dirs['config_path'], 'w', encoding='utf-8') as f:
            json.dump({
                'app': {'name': 'Original', 'version': '1.0'},
                'settings': {'theme': 'dark'}
            }, f)

        # Create source config
        source_dir = tempfile.mkdtemp()
        with open(os.path.join(source_dir, 'config.json'), 'w') as f:
            json.dump({
                'app': {'name': 'Updated', 'new_setting': 'value'},
                'extra': 'data'
            }, f)

        result = import_export_service._merge_import(source_dir)

        assert result['success'] is True

        # Verify deep merge
        with open(temp_dirs['config_path'], 'r', encoding='utf-8') as f:
            config = json.load(f)
        assert config['app']['name'] == 'Updated'  # Overwritten
        assert config['app']['version'] == '1.0'  # Preserved
        assert config['app']['new_setting'] == 'value'  # Added
        assert config['settings']['theme'] == 'dark'  # Preserved
        assert config['extra'] == 'data'  # Added

        shutil.rmtree(source_dir, ignore_errors=True)


class TestOverwriteImport:
    """Test _overwrite_import method."""

    def test_overwrite_scripts_directory(self, import_export_service, temp_dirs):
        """Test overwriting scripts directory."""
        # Create existing script
        existing_script = os.path.join(temp_dirs['scripts_dir'], 'existing.py')
        with open(existing_script, 'w') as f:
            f.write('existing')

        # Create source directory with different script
        source_dir = tempfile.mkdtemp()
        source_scripts = os.path.join(source_dir, 'scripts')
        os.makedirs(source_scripts)
        with open(os.path.join(source_scripts, 'new_script.py'), 'w') as f:
            f.write('new')

        result = import_export_service._overwrite_import(source_dir)

        assert result['success'] is True
        assert os.path.exists(os.path.join(temp_dirs['scripts_dir'], 'new_script.py'))
        # Existing script should be gone
        assert not os.path.exists(existing_script)

        shutil.rmtree(source_dir, ignore_errors=True)

    def test_overwrite_config(self, import_export_service, temp_dirs):
        """Test overwriting configuration file."""
        # Set up existing config
        with open(temp_dirs['config_path'], 'w', encoding='utf-8') as f:
            json.dump({'existing': 'data', 'old_key': 'old_value'}, f)

        # Create source config
        source_dir = tempfile.mkdtemp()
        with open(os.path.join(source_dir, 'config.json'), 'w') as f:
            json.dump({'new': 'data', 'new_key': 'new_value'}, f)

        result = import_export_service._overwrite_import(source_dir)

        assert result['success'] is True

        # Verify complete overwrite
        with open(temp_dirs['config_path'], 'r', encoding='utf-8') as f:
            config = json.load(f)
        assert config == {'new': 'data', 'new_key': 'new_value'}
        assert 'existing' not in config
        assert 'old_key' not in config

        shutil.rmtree(source_dir, ignore_errors=True)


class TestDatabaseMerge:
    """Test database merge functionality."""

    def test_merge_database_new_records(self, import_export_service, temp_dirs):
        """Test merging database with new records."""
        # Create source database with additional records
        source_db = os.path.join(temp_dirs['base_dir'], 'source.db')
        conn = sqlite3.connect(source_db)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scripts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                content TEXT,
                target_app TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute("INSERT INTO scripts (name, content, target_app) VALUES ('NewScript', 'new_content', 'javascript')")
        conn.commit()
        conn.close()

        # Import the source database
        source_dir = tempfile.mkdtemp()
        shutil.copy2(source_db, os.path.join(source_dir, 'scripts.db'))

        result = import_export_service._merge_import(source_dir)

        assert result['success'] is True

        # Verify both records exist
        conn = sqlite3.connect(temp_dirs['db_path'])
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM scripts ORDER BY name')
        names = [row[0] for row in cursor.fetchall()]
        conn.close()

        assert 'TestScript' in names
        assert 'NewScript' in names

        shutil.rmtree(source_dir, ignore_errors=True)
        os.unlink(source_db)

    def test_merge_database_update_existing(self, import_export_service, temp_dirs):
        """Test merging database updates existing records."""
        # Create source database with updated record (same name, different content)
        source_db = os.path.join(temp_dirs['base_dir'], 'source.db')
        conn = sqlite3.connect(source_db)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scripts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                content TEXT,
                target_app TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Same name as existing but different content
        cursor.execute("INSERT INTO scripts (name, content, target_app) VALUES ('TestScript', 'updated_content', 'python')")
        conn.commit()
        conn.close()

        # Import the source database
        source_dir = tempfile.mkdtemp()
        shutil.copy2(source_db, os.path.join(source_dir, 'scripts.db'))

        result = import_export_service._merge_import(source_dir)

        assert result['success'] is True

        # Verify record was updated
        conn = sqlite3.connect(temp_dirs['db_path'])
        cursor = conn.cursor()
        cursor.execute('SELECT content FROM scripts WHERE name = ?', ('TestScript',))
        content = cursor.fetchone()[0]
        conn.close()

        assert content == 'updated_content'

        shutil.rmtree(source_dir, ignore_errors=True)
        os.unlink(source_db)
