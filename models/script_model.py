"""ScriptModel data model for script management."""

import sqlite3
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from models.repository import Repository


class ScriptType(str, Enum):
    """Enumeration of script types."""
    PYTHON = 'python'
    WPS = 'wps'
    JAVASCRIPT = 'javascript'


class ScriptModel(Repository):
    """Model for managing scripts, dependencies, and mappings.

    This model provides CRUD operations for scripts and manages:
    - scripts: Main script storage with hierarchical structure
    - dependencies: Python package dependencies for scripts
    - wps_mappings: WPS Office ribbon button mappings
    - js_bookmarks: JavaScript bookmark associations
    - config: Application configuration storage
    """

    def create_tables(self) -> None:
        """Create all database tables if they don't exist."""
        # scripts table
        self.execute("""
            CREATE TABLE IF NOT EXISTS scripts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                script_type TEXT NOT NULL,
                code TEXT NOT NULL,
                description TEXT DEFAULT '',
                parent_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES scripts(id) ON DELETE CASCADE
            )
        """)

        # dependencies table
        self.execute("""
            CREATE TABLE IF NOT EXISTS dependencies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                script_id INTEGER NOT NULL,
                package_name TEXT NOT NULL,
                version TEXT NOT NULL,
                installed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (script_id) REFERENCES scripts(id) ON DELETE CASCADE
            )
        """)

        # wps_mappings table
        self.execute("""
            CREATE TABLE IF NOT EXISTS wps_mappings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                script_id INTEGER NOT NULL,
                ribbon_tab TEXT NOT NULL,
                ribbon_group TEXT NOT NULL,
                button_label TEXT NOT NULL,
                function_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (script_id) REFERENCES scripts(id) ON DELETE CASCADE
            )
        """)

        # js_bookmarks table
        self.execute("""
            CREATE TABLE IF NOT EXISTS js_bookmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                script_id INTEGER NOT NULL,
                bookmark_name TEXT NOT NULL,
                bookmark_url TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (script_id) REFERENCES scripts(id) ON DELETE CASCADE
            )
        """)

        # config table
        self.execute("""
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

    # ==================== Script CRUD Operations ====================

    def add_script(
        self,
        name: str,
        script_type: ScriptType,
        code: str,
        description: str = '',
        parent_id: Optional[int] = None
    ) -> int:
        """Add a new script.

        Args:
            name: Script name.
            script_type: Type of script (PYTHON, WPS, or JAVASCRIPT).
            code: Script source code.
            description: Script description.
            parent_id: Optional parent script ID for hierarchical structure.

        Returns:
            The ID of the newly created script.
        """
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.execute("""
            INSERT INTO scripts (name, script_type, code, description, parent_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, script_type.value, code, description, parent_id, now, now))

        # Get the last inserted ID
        cursor = self.conn.execute("SELECT last_insert_rowid()")
        return cursor.fetchone()[0]

    def get_script(self, script_id: int) -> Optional[sqlite3.Row]:
        """Get a script by ID.

        Args:
            script_id: The script ID.

        Returns:
            The script row or None if not found.
        """
        return self.query_one("SELECT * FROM scripts WHERE id = ?", (script_id,))

    def get_tree(self, script_type: ScriptType) -> list:
        """Get scripts as a tree structure.

        Args:
            script_type: Filter by script type.

        Returns:
            A list of dictionaries representing the script tree.
        """
        # Get all scripts of the specified type
        scripts = self.query(
            "SELECT * FROM scripts WHERE script_type = ?",
            (script_type.value,)
        )

        # Build tree structure
        script_dict = {}
        roots = []

        for script in scripts:
            script_id = script['id']
            script_dict[script_id] = dict(script)
            script_dict[script_id]['children'] = []

        for script in scripts:
            parent_id = script['parent_id']
            if parent_id is None:
                roots.append(script_dict[script['id']])
            elif parent_id in script_dict:
                script_dict[parent_id]['children'].append(script_dict[script['id']])

        return roots

    def update_script(self, script_id: int, **kwargs: Any) -> None:
        """Update a script.

        Args:
            script_id: The script ID to update.
            **kwargs: Fields to update (name, code, description, parent_id).
        """
        if not kwargs:
            return

        # Build dynamic update query
        fields = []
        values = []
        for key, value in kwargs.items():
            if key in ('name', 'code', 'description', 'parent_id'):
                fields.append(f"{key} = ?")
                if isinstance(value, ScriptType):
                    values.append(value.value)
                else:
                    values.append(value)

        if fields:
            values.append(script_id)
            fields_str = ", ".join(fields)
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            # Insert now before the last element (script_id)
            values.insert(-1, now)
            self.execute(f"""
                UPDATE scripts SET {fields_str}, updated_at = ?
                WHERE id = ?
            """, tuple(values))

    def delete_script(self, script_id: int) -> None:
        """Delete a script.

        Args:
            script_id: The script ID to delete.
        """
        self.execute("DELETE FROM scripts WHERE id = ?", (script_id,))

    # ==================== Config Operations ====================

    def get_config(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a configuration value.

        Args:
            key: Configuration key.
            default: Default value if key not found.

        Returns:
            Configuration value or default.
        """
        row = self.query_one("SELECT value FROM config WHERE key = ?", (key,))
        if row:
            return row['value']
        return default

    def set_config(self, key: str, value: str) -> None:
        """Set a configuration value.

        Args:
            key: Configuration key.
            value: Configuration value.
        """
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.execute("""
            INSERT INTO config (key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = ?
        """, (key, value, now, now))

    # ==================== Dependency Operations ====================

    def add_dependency(
        self,
        script_id: int,
        package_name: str,
        version: str,
        installed: bool = False
    ) -> int:
        """Add a dependency for a script.

        Args:
            script_id: The script ID.
            package_name: Python package name.
            version: Required version.
            installed: Whether the package is installed.

        Returns:
            The ID of the newly created dependency.
        """
        self.execute("""
            INSERT INTO dependencies (script_id, package_name, version, installed)
            VALUES (?, ?, ?, ?)
        """, (script_id, package_name, version, 1 if installed else 0))

        cursor = self.conn.execute("SELECT last_insert_rowid()")
        return cursor.fetchone()[0]

    def get_dependencies(self, script_id: int) -> list:
        """Get all dependencies for a script.

        Args:
            script_id: The script ID.

        Returns:
            A list of dependency rows.
        """
        return self.query(
            "SELECT * FROM dependencies WHERE script_id = ?",
            (script_id,)
        )

    # ==================== WPS Mapping Operations ====================

    def add_wps_mapping(
        self,
        script_id: int,
        ribbon_tab: str,
        ribbon_group: str,
        button_label: str,
        function_name: str
    ) -> int:
        """Add a WPS ribbon mapping for a script.

        Args:
            script_id: The script ID.
            ribbon_tab: WPS ribbon tab name (e.g., "Home", "Insert").
            ribbon_group: Ribbon group name.
            button_label: Button display label.
            function_name: Function to call when button clicked.

        Returns:
            The ID of the newly created mapping.
        """
        self.execute("""
            INSERT INTO wps_mappings (script_id, ribbon_tab, ribbon_group, button_label, function_name)
            VALUES (?, ?, ?, ?, ?)
        """, (script_id, ribbon_tab, ribbon_group, button_label, function_name))

        cursor = self.conn.execute("SELECT last_insert_rowid()")
        return cursor.fetchone()[0]

    def get_wps_mappings(self, script_id: int) -> list:
        """Get all WPS mappings for a script.

        Args:
            script_id: The script ID.

        Returns:
            A list of WPS mapping rows.
        """
        return self.query(
            "SELECT * FROM wps_mappings WHERE script_id = ?",
            (script_id,)
        )

    def get_all_wps_scripts(self) -> list:
        """Get all WPS scripts with their mappings.

        Returns:
            A list of WPS scripts with associated mappings.
        """
        wps_scripts = self.query(
            "SELECT * FROM scripts WHERE script_type = ?",
            (ScriptType.WPS.value,)
        )

        result = []
        for script in wps_scripts:
            script_dict = dict(script)
            script_dict['mappings'] = self.get_wps_mappings(script['id'])
            result.append(script_dict)

        return result

    # ==================== JS Bookmark Operations ====================

    def add_js_bookmark(
        self,
        script_id: int,
        bookmark_name: str,
        bookmark_url: str
    ) -> int:
        """Add a bookmark for a JS script.

        Args:
            script_id: The script ID.
            bookmark_name: Bookmark display name.
            bookmark_url: Bookmark URL.

        Returns:
            The ID of the newly created bookmark.
        """
        self.execute("""
            INSERT INTO js_bookmarks (script_id, bookmark_name, bookmark_url)
            VALUES (?, ?, ?)
        """, (script_id, bookmark_name, bookmark_url))

        cursor = self.conn.execute("SELECT last_insert_rowid()")
        return cursor.fetchone()[0]

    def get_js_bookmarks(self, script_id: int) -> list:
        """Get all bookmarks for a JS script.

        Args:
            script_id: The script ID.

        Returns:
            A list of bookmark rows.
        """
        return self.query(
            "SELECT * FROM js_bookmarks WHERE script_id = ?",
            (script_id,)
        )

    def get_all_js_scripts(self) -> list:
        """Get all JS scripts with their bookmarks.

        Returns:
            A list of JS scripts with associated bookmarks.
        """
        js_scripts = self.query(
            "SELECT * FROM scripts WHERE script_type = ?",
            (ScriptType.JAVASCRIPT.value,)
        )

        result = []
        for script in js_scripts:
            script_dict = dict(script)
            script_dict['bookmarks'] = self.get_js_bookmarks(script['id'])
            result.append(script_dict)

        return result
