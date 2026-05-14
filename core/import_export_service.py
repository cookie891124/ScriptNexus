"""ImportExportService for backup and restore of scripts and configurations."""

import json
import os
import shutil
import sqlite3
import tempfile
import zipfile
from datetime import datetime
from typing import Any, Dict, Optional


class ImportExportService:
    """Service for exporting and importing scripts, configurations, and templates."""

    def __init__(self, scripts_dir: str, config_path: str, db_path: str, templates_dir: str):
        """Initialize ImportExportService with directory and file paths.

        Args:
            scripts_dir: Path to the scripts directory.
            config_path: Path to the config.json file.
            db_path: Path to the scripts.db SQLite database.
            templates_dir: Path to the templates directory.
        """
        self.scripts_dir = scripts_dir
        self.config_path = config_path
        self.db_path = db_path
        self.templates_dir = templates_dir

    def export_all(self) -> Dict[str, Any]:
        """Export all configurations and scripts to a ZIP archive.

        Creates a ZIP file containing:
        - scripts/ directory
        - data/config.json
        - data/scripts.db
        - templates/

        Returns:
            Export result dictionary:
            {
                'success': True/False,
                'zip_path': '/path/to/backup.zip' or None,
                'error': 'error message' or None
            }
        """
        result = {
            'success': False,
            'zip_path': None,
            'error': None
        }

        try:
            # Create temporary directory for export
            temp_dir = tempfile.mkdtemp(prefix='wps_export_')

            try:
                # Copy scripts directory
                if os.path.exists(self.scripts_dir):
                    dest_scripts = os.path.join(temp_dir, 'scripts')
                    shutil.copytree(self.scripts_dir, dest_scripts)

                # Copy config.json
                if os.path.exists(self.config_path):
                    dest_config = os.path.join(temp_dir, 'config.json')
                    shutil.copy2(self.config_path, dest_config)

                # Copy database
                if os.path.exists(self.db_path):
                    dest_db = os.path.join(temp_dir, 'scripts.db')
                    shutil.copy2(self.db_path, dest_db)

                # Copy templates directory
                if os.path.exists(self.templates_dir):
                    dest_templates = os.path.join(temp_dir, 'templates')
                    shutil.copytree(self.templates_dir, dest_templates)

                # Create ZIP file
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                zip_filename = f'scripts_backup_{timestamp}.zip'

                # Determine output directory (same as config directory)
                output_dir = os.path.dirname(self.config_path) or os.getcwd()
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir, exist_ok=True)

                zip_path = os.path.join(output_dir, zip_filename)

                # Create ZIP archive
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, temp_dir)
                            zipf.write(file_path, arcname)

                result['success'] = True
                result['zip_path'] = zip_path

            finally:
                # Clean up temporary directory
                shutil.rmtree(temp_dir, ignore_errors=True)

        except Exception as e:
            result['error'] = str(e)

        return result

    def import_package(self, zip_path: str, merge: bool = True) -> Dict[str, Any]:
        """Import a backup package from a ZIP archive.

        Args:
            zip_path: Path to the ZIP backup file.
            merge: If True, merge with existing data. If False, overwrite.

        Returns:
            Import result dictionary:
            {
                'success': True/False,
                'imported_files': list of imported files,
                'error': 'error message' or None
            }
        """
        result = {
            'success': False,
            'imported_files': [],
            'error': None
        }

        try:
            # Verify ZIP file exists
            if not os.path.exists(zip_path):
                result['error'] = f'ZIP file not found: {zip_path}'
                return result

            if not zipfile.is_zipfile(zip_path):
                result['error'] = f'Not a valid ZIP file: {zip_path}'
                return result

            # Extract to temporary directory
            temp_dir = tempfile.mkdtemp(prefix='wps_import_')

            try:
                with zipfile.ZipFile(zip_path, 'r') as zipf:
                    zipf.extractall(temp_dir)

                # Validate structure
                validation = self._validate_structure(temp_dir)
                if not validation['valid']:
                    result['error'] = validation['error']
                    return result

                # Perform import
                if merge:
                    import_result = self._merge_import(temp_dir)
                else:
                    import_result = self._overwrite_import(temp_dir)

                result['success'] = import_result['success']
                result['imported_files'] = import_result['imported_files']
                if import_result.get('error'):
                    result['error'] = import_result['error']

            finally:
                # Clean up temporary directory
                shutil.rmtree(temp_dir, ignore_errors=True)

        except Exception as e:
            result['error'] = str(e)

        return result

    def _validate_structure(self, directory: str) -> Dict[str, Any]:
        """Validate the structure of an import package.

        Args:
            directory: Path to the extracted package directory.

        Returns:
            Validation result dictionary:
            {
                'valid': True/False,
                'error': 'error message' or None,
                'found_files': list of found files/directories
            }
        """
        result = {
            'valid': False,
            'error': None,
            'found_files': []
        }

        try:
            # Check for expected directories and files
            has_scripts = os.path.isdir(os.path.join(directory, 'scripts'))
            has_config = os.path.isfile(os.path.join(directory, 'config.json'))
            has_db = os.path.isfile(os.path.join(directory, 'scripts.db'))
            has_templates = os.path.isdir(os.path.join(directory, 'templates'))

            # Collect found items
            if has_scripts:
                result['found_files'].append('scripts/')
            if has_config:
                result['found_files'].append('config.json')
            if has_db:
                result['found_files'].append('scripts.db')
            if has_templates:
                result['found_files'].append('templates/')

            # At minimum, we need config.json or scripts.db to consider it valid
            if not (has_config or has_db):
                result['error'] = 'Invalid backup package: missing config.json and scripts.db'
                return result

            result['valid'] = True

        except Exception as e:
            result['error'] = str(e)

        return result

    def _merge_import(self, directory: str) -> Dict[str, Any]:
        """Merge imported data with existing data.

        Args:
            directory: Path to the extracted package directory.

        Returns:
            Import result dictionary:
            {
                'success': True/False,
                'imported_files': list of imported files,
                'error': 'error message' or None
            }
        """
        result = {
            'success': False,
            'imported_files': [],
            'error': None
        }

        try:
            # Merge scripts directory
            src_scripts = os.path.join(directory, 'scripts')
            if os.path.exists(src_scripts):
                dest_scripts = self.scripts_dir
                if not os.path.exists(dest_scripts):
                    os.makedirs(dest_scripts, exist_ok=True)
                self._merge_directory(src_scripts, dest_scripts)
                result['imported_files'].append('scripts/')

            # Merge config.json
            src_config = os.path.join(directory, 'config.json')
            if os.path.exists(src_config):
                self._merge_config(src_config)
                result['imported_files'].append('config.json')

            # Merge database
            src_db = os.path.join(directory, 'scripts.db')
            if os.path.exists(src_db):
                self._merge_database(src_db)
                result['imported_files'].append('scripts.db')

            # Merge templates directory
            src_templates = os.path.join(directory, 'templates')
            if os.path.exists(src_templates):
                dest_templates = self.templates_dir
                if not os.path.exists(dest_templates):
                    os.makedirs(dest_templates, exist_ok=True)
                self._merge_directory(src_templates, dest_templates)
                result['imported_files'].append('templates/')

            result['success'] = True

        except Exception as e:
            result['error'] = str(e)

        return result

    def _overwrite_import(self, directory: str) -> Dict[str, Any]:
        """Overwrite existing data with imported data.

        Args:
            directory: Path to the extracted package directory.

        Returns:
            Import result dictionary:
            {
                'success': True/False,
                'imported_files': list of imported files,
                'error': 'error message' or None
            }
        """
        result = {
            'success': False,
            'imported_files': [],
            'error': None
        }

        try:
            # Overwrite scripts directory
            src_scripts = os.path.join(directory, 'scripts')
            if os.path.exists(src_scripts):
                dest_scripts = self.scripts_dir
                if os.path.exists(dest_scripts):
                    shutil.rmtree(dest_scripts)
                shutil.copytree(src_scripts, dest_scripts)
                result['imported_files'].append('scripts/')

            # Overwrite config.json
            src_config = os.path.join(directory, 'config.json')
            if os.path.exists(src_config):
                shutil.copy2(src_config, self.config_path)
                result['imported_files'].append('config.json')

            # Overwrite database
            src_db = os.path.join(directory, 'scripts.db')
            if os.path.exists(src_db):
                shutil.copy2(src_db, self.db_path)
                result['imported_files'].append('scripts.db')

            # Overwrite templates directory
            src_templates = os.path.join(directory, 'templates')
            if os.path.exists(src_templates):
                dest_templates = self.templates_dir
                if os.path.exists(dest_templates):
                    shutil.rmtree(dest_templates)
                shutil.copytree(src_templates, dest_templates)
                result['imported_files'].append('templates/')

            result['success'] = True

        except Exception as e:
            result['error'] = str(e)

        return result

    def _merge_directory(self, src: str, dest: str) -> None:
        """Recursively merge source directory into destination.

        Args:
            src: Source directory path.
            dest: Destination directory path.
        """
        if not os.path.exists(dest):
            os.makedirs(dest, exist_ok=True)

        for item in os.listdir(src):
            src_item = os.path.join(src, item)
            dest_item = os.path.join(dest, item)

            if os.path.isdir(src_item):
                self._merge_directory(src_item, dest_item)
            else:
                # File exists in source, copy it (overwrite if exists)
                shutil.copy2(src_item, dest_item)

    def _merge_config(self, src_config: str) -> None:
        """Merge source config with existing config.

        Args:
            src_config: Path to source config.json file.
        """
        # Load existing config
        existing_config = {}
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    existing_config = json.load(f)
            except (json.JSONDecodeError, IOError):
                existing_config = {}

        # Load source config
        with open(src_config, 'r', encoding='utf-8') as f:
            src_config_data = json.load(f)

        # Deep merge: source values override existing
        merged = self._deep_merge(existing_config, src_config_data)

        # Save merged config
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)

    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """Recursively merge two dictionaries.

        Args:
            base: Base dictionary.
            override: Dictionary with values to override.

        Returns:
            Merged dictionary.
        """
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def _merge_database(self, src_db: str) -> None:
        """Merge source database with existing database.

        Merges records based on unique business keys (e.g., name for scripts table)
        rather than auto-increment IDs to avoid conflicts.

        Args:
            src_db: Path to source database file.
        """
        if not os.path.exists(self.db_path):
            # If destination doesn't exist, just copy
            shutil.copy2(src_db, self.db_path)
            return

        # Connect to both databases
        src_conn = sqlite3.connect(src_db)
        dest_conn = sqlite3.connect(self.db_path)

        try:
            src_cursor = src_conn.cursor()
            dest_cursor = dest_conn.cursor()

            # Get list of tables from source
            src_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in src_cursor.fetchall()]

            for table in tables:
                if table.startswith('sqlite_'):
                    continue

                # Get table schema info
                src_cursor.execute(f'PRAGMA table_info({table})')
                columns = src_cursor.fetchall()
                column_names = [col[1] for col in columns]

                # Find primary key column(s)
                pk_columns = [col[1] for col in columns if col[5] == 1]  # col[5] is pk flag

                # Get all data from source table
                src_cursor.execute(f'SELECT * FROM {table}')
                rows = src_cursor.fetchall()

                if not rows:
                    continue

                # Check if destination table exists and has same structure
                dest_cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
                if not dest_cursor.fetchone():
                    # Table doesn't exist in destination, create it
                    src_cursor.execute(f'SELECT sql FROM sqlite_master WHERE type=? AND name=?', ('table', table))
                    create_sql = src_cursor.fetchone()[0]
                    dest_cursor.execute(create_sql)

                for row in rows:
                    if pk_columns and 'id' in pk_columns and len(pk_columns) == 1:
                        # Auto-increment ID case: exclude ID from match, use other columns
                        # For scripts table, match on 'name' column
                        non_pk_columns = [c for c in column_names if c not in pk_columns]
                        if 'name' in non_pk_columns:
                            # Check if record exists by name
                            name_idx = column_names.index('name')
                            name_value = row[name_idx]

                            dest_cursor.execute(f'SELECT COUNT(*) FROM {table} WHERE name = ?', (name_value,))
                            if dest_cursor.fetchone()[0] > 0:
                                # Update existing record (exclude id from update)
                                update_cols = [c for c in column_names if c != 'id']
                                set_clause = ', '.join([f'{col} = ?' for col in update_cols])
                                update_values = [row[column_names.index(col)] for col in update_cols] + [name_value]
                                dest_cursor.execute(f'UPDATE {table} SET {set_clause} WHERE name = ?', update_values)
                            else:
                                # Insert new record (let auto-increment assign id)
                                insert_cols = [c for c in column_names if c != 'id']
                                placeholders = ', '.join(['?' for _ in insert_cols])
                                insert_values = [row[column_names.index(col)] for col in insert_cols]
                                dest_cursor.execute(f'INSERT INTO {table} ({", ".join(insert_cols)}) VALUES ({placeholders})', insert_values)
                        else:
                            # No name column, use INSERT OR REPLACE
                            placeholders = ', '.join(['?' for _ in column_names])
                            dest_cursor.execute(
                                f'INSERT OR REPLACE INTO {table} ({", ".join(column_names)}) VALUES ({placeholders})',
                                row
                            )
                    else:
                        # No auto-increment ID, use INSERT OR REPLACE
                        placeholders = ', '.join(['?' for _ in column_names])
                        dest_cursor.execute(
                            f'INSERT OR REPLACE INTO {table} ({", ".join(column_names)}) VALUES ({placeholders})',
                            row
                        )

            dest_conn.commit()

        finally:
            src_conn.close()
            dest_conn.close()
