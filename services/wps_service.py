"""WPS script service for managing WPS Office scripts and templates."""

import os
import sqlite3
import zipfile
from typing import Optional, List, Dict, Any
from datetime import datetime
from xml.sax.saxutils import escape as xml_escape


class WpsService:
    """Service for managing WPS Office scripts with Ribbon UI integration."""

    def __init__(self, db_path: str):
        """Initialize the WPS service.

        Args:
            db_path: Path to the SQLite database file.
        """
        self.db_path = db_path
        self.templates_dir: Optional[str] = None
        self.word_startup: Optional[str] = None
        self.excel_startup: Optional[str] = None
        self._init_db()

    def _init_db(self) -> None:
        """Initialize the database schema with migration support."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # ===== 功能区结构表 =====

            # ribbon_tabs - 功能区 Tab
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='ribbon_tabs'
            """)
            if not cursor.fetchone():
                cursor.execute("""
                    CREATE TABLE ribbon_tabs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        target_app TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                print("[DB] Created ribbon_tabs table")

            # ribbon_groups - 功能区 Group
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='ribbon_groups'
            """)
            if not cursor.fetchone():
                cursor.execute("""
                    CREATE TABLE ribbon_groups (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        tab_id INTEGER,
                        target_app TEXT NOT NULL,
                        position INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (tab_id) REFERENCES ribbon_tabs(id)
                    )
                """)
                print("[DB] Created ribbon_groups table")

            # ribbon_buttons - 功能区 Button
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='ribbon_buttons'
            """)
            if not cursor.fetchone():
                cursor.execute("""
                    CREATE TABLE ribbon_buttons (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        label TEXT NOT NULL,
                        group_id INTEGER,
                        script_id INTEGER DEFAULT NULL,
                        target_app TEXT NOT NULL,
                        position INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (group_id) REFERENCES ribbon_groups(id),
                        FOREIGN KEY (script_id) REFERENCES wps_scripts(id)
                    )
                """)
                print("[DB] Created ribbon_buttons table")

            # Migrate: add position column to existing ribbon tables
            for table in ['ribbon_groups', 'ribbon_buttons']:
                try:
                    cursor.execute(f"SELECT position FROM {table} LIMIT 0")
                except sqlite3.OperationalError:
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN position INTEGER DEFAULT 0")

            # ===== 脚本表 =====

            # Check if wps_scripts table exists
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='wps_scripts'
            """)
            table_exists = cursor.fetchone() is not None

            if not table_exists:
                # Fresh database - create the table
                cursor.execute("""
                    CREATE TABLE wps_scripts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        js_code TEXT NOT NULL,
                        target_app TEXT NOT NULL,
                        main_function TEXT DEFAULT '',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                print("[DB] Created new wps_scripts table")
            else:
                # Table exists - check current schema
                cursor.execute("PRAGMA table_info(wps_scripts)")
                columns = {col[1] for col in cursor.fetchall()}

                # Add main_function column if missing
                if 'main_function' not in columns:
                    cursor.execute("ALTER TABLE wps_scripts ADD COLUMN main_function TEXT DEFAULT ''")
                    print("[Migration] Added main_function column")

                # Check if we need to rebuild the table (for old vba_code or ribbon columns)
                needs_rebuild = 'vba_code' in columns or 'ribbon_tab' in columns

                if needs_rebuild:
                    # Get existing data
                    cursor.execute("SELECT * FROM wps_scripts")
                    rows = cursor.fetchall()
                    cursor.execute("PRAGMA table_info(wps_scripts)")
                    old_cols = [col[1] for col in cursor.fetchall()]

                    # Drop old table
                    cursor.execute("DROP TABLE wps_scripts")

                    # Create new table (without ribbon columns - they moved to separate tables)
                    cursor.execute("""
                        CREATE TABLE wps_scripts (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name TEXT NOT NULL,
                            js_code TEXT NOT NULL,
                            target_app TEXT NOT NULL,
                            main_function TEXT DEFAULT '',
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)

                    # Insert data back with mapping
                    for row in rows:
                        row_dict = dict(zip(old_cols, row))
                        name = row_dict.get('name', '')
                        # Map vba_code to js_code
                        js_code = row_dict.get('js_code') or row_dict.get('vba_code', '')
                        target_app = row_dict.get('target_app', 'word')
                        main_function = row_dict.get('main_function', '')

                        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        cursor.execute("""
                            INSERT INTO wps_scripts (name, js_code, target_app, main_function, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (name, js_code, target_app, main_function, now, now))

                    print(f"[Migration] Rebuilt wps_scripts table ({len(rows)} rows) - removed ribbon columns")

            conn.commit()

        finally:
            conn.close()

    def set_paths(self, templates_dir: str, word_startup: Optional[str],
                  excel_startup: Optional[str]) -> None:
        """Set the template and startup paths.

        Args:
            templates_dir: Directory for storing template files.
            word_startup: WPS Word startup directory path.
            excel_startup: WPS Excel startup directory path.
        """
        # Only set templates_dir if it's non-empty
        if templates_dir and templates_dir.strip():
            if not os.path.exists(templates_dir):
                os.makedirs(templates_dir)
            self.templates_dir = templates_dir
        self.word_startup = word_startup
        self.excel_startup = excel_startup

    def add_script(self, name: str, js_code: str, target_app: str,
                   main_function: str = "") -> int:
        """Add a new WPS script.

        Args:
            name: Script name.
            js_code: JS macro code content.
            target_app: Target application ('word' or 'excel').
            main_function: Main function description for display.

        Returns:
            The ID of the newly created script.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("""
            INSERT INTO wps_scripts (name, js_code, target_app, main_function, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, js_code, target_app, main_function, now, now))

        script_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return script_id

    def get_script(self, script_id: int) -> Optional[Dict[str, Any]]:
        """Get a script by ID.

        Args:
            script_id: The script ID.

        Returns:
            Script data as a dictionary, or None if not found.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, js_code, target_app, main_function, created_at, updated_at
            FROM wps_scripts
            WHERE id = ?
        """, (script_id,))

        row = cursor.fetchone()
        conn.close()

        if row is None:
            return None

        return dict(row)

    def get_all_scripts(self, target_app: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all WPS scripts.

        Args:
            target_app: Optional filter by target application ('word' or 'excel').

        Returns:
            List of script data dictionaries.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if target_app:
            cursor.execute("""
                SELECT id, name, js_code, target_app, main_function, created_at, updated_at
                FROM wps_scripts
                WHERE target_app = ?
                ORDER BY name
            """, (target_app,))
        else:
            cursor.execute("""
                SELECT id, name, js_code, target_app, main_function, created_at, updated_at
                FROM wps_scripts
                ORDER BY name
            """)

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def update_script(self, script_id: int, **kwargs) -> bool:
        """Update a script.

        Args:
            script_id: The script ID.
            **kwargs: Fields to update (name, js_code, target_app, main_function).

        Returns:
            True if updated successfully, False otherwise.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check if script exists
        cursor.execute("SELECT id FROM wps_scripts WHERE id = ?", (script_id,))
        if cursor.fetchone() is None:
            conn.close()
            return False

        # Build update query
        allowed_fields = {"name", "js_code", "target_app", "main_function"}
        updates = []
        values = []

        for key, value in kwargs.items():
            if key in allowed_fields:
                updates.append(f"{key} = ?")
                values.append(value)

        if not updates:
            conn.close()
            return False

        values.append(script_id)
        updates.append("updated_at = ?")
        values.insert(-1, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        query = f"""
            UPDATE wps_scripts
            SET {", ".join(updates)}
            WHERE id = ?
        """

        cursor.execute(query, values)
        conn.commit()
        conn.close()

        return True

    def delete_script(self, script_id: int) -> bool:
        """Delete a script.

        Args:
            script_id: The script ID.

        Returns:
            True if deleted successfully, False otherwise.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check if script exists
        cursor.execute("SELECT id FROM wps_scripts WHERE id = ?", (script_id,))
        if cursor.fetchone() is None:
            conn.close()
            return False

        cursor.execute("DELETE FROM wps_scripts WHERE id = ?", (script_id,))
        conn.commit()
        conn.close()

        return True

    # ===== 功能区 Tab CRUD =====

    def add_tab(self, name: str, target_app: str) -> int:
        """Add a new ribbon tab.

        Args:
            name: Tab name.
            target_app: Target application ('word' or 'excel').

        Returns:
            The ID of the newly created tab.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO ribbon_tabs (name, target_app)
            VALUES (?, ?)
        """, (name, target_app))

        tab_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return tab_id

    def get_tab(self, tab_id: int) -> Optional[Dict[str, Any]]:
        """Get a ribbon tab by ID."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, target_app, created_at
            FROM ribbon_tabs
            WHERE id = ?
        """, (tab_id,))

        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None

    def get_all_tabs(self, target_app: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all ribbon tabs."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if target_app:
            cursor.execute("""
                SELECT id, name, target_app, created_at
                FROM ribbon_tabs
                WHERE target_app = ?
                ORDER BY name
            """, (target_app,))
        else:
            cursor.execute("""
                SELECT id, name, target_app, created_at
                FROM ribbon_tabs
                ORDER BY name
            """)

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def update_tab(self, tab_id: int, name: str) -> bool:
        """Update a ribbon tab name."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("UPDATE ribbon_tabs SET name = ? WHERE id = ?", (name, tab_id))
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()

        return success

    def delete_tab(self, tab_id: int) -> bool:
        """Delete a ribbon tab and all its groups/buttons."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Delete child buttons (through groups)
        cursor.execute("""
            DELETE FROM ribbon_buttons
            WHERE group_id IN (SELECT id FROM ribbon_groups WHERE tab_id = ?)
        """, (tab_id,))

        # Delete child groups
        cursor.execute("DELETE FROM ribbon_groups WHERE tab_id = ?", (tab_id,))

        # Delete tab
        cursor.execute("DELETE FROM ribbon_tabs WHERE id = ?", (tab_id,))
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()

        return success

    # ===== 功能区 Group CRUD =====

    def add_group(self, name: str, tab_id: int, target_app: str) -> int:
        """Add a new ribbon group."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Set position to end of list
        cursor.execute(
            "SELECT COALESCE(MAX(position), -1) + 1 FROM ribbon_groups WHERE tab_id = ?",
            (tab_id,)
        )
        pos = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO ribbon_groups (name, tab_id, target_app, position)
            VALUES (?, ?, ?, ?)
        """, (name, tab_id, target_app, pos))

        group_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return group_id

    def get_group(self, group_id: int) -> Optional[Dict[str, Any]]:
        """Get a ribbon group by ID."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, tab_id, target_app, created_at
            FROM ribbon_groups
            WHERE id = ?
        """, (group_id,))

        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None

    def get_all_groups(self, tab_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all ribbon groups, optionally filtered by tab."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if tab_id:
            cursor.execute("""
                SELECT id, name, tab_id, target_app, created_at
                FROM ribbon_groups
                WHERE tab_id = ?
                ORDER BY position, name
            """, (tab_id,))
        else:
            cursor.execute("""
                SELECT id, name, tab_id, target_app, created_at
                FROM ribbon_groups
                ORDER BY position, name
            """)

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def update_group(self, group_id: int, name: str) -> bool:
        """Update a ribbon group name."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("UPDATE ribbon_groups SET name = ? WHERE id = ?", (name, group_id))
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()

        return success

    def delete_group(self, group_id: int) -> bool:
        """Delete a ribbon group and all its buttons."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Delete child buttons
        cursor.execute("DELETE FROM ribbon_buttons WHERE group_id = ?", (group_id,))

        # Delete group
        cursor.execute("DELETE FROM ribbon_groups WHERE id = ?", (group_id,))
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()

        return success

    # ===== 功能区 Button CRUD =====

    def add_button(self, label: str, group_id: int, target_app: str) -> int:
        """Add a new ribbon button (without script binding)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Set position to end of list
        cursor.execute(
            "SELECT COALESCE(MAX(position), -1) + 1 FROM ribbon_buttons WHERE group_id = ?",
            (group_id,)
        )
        pos = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO ribbon_buttons (label, group_id, target_app, position)
            VALUES (?, ?, ?, ?)
        """, (label, group_id, target_app, pos))

        button_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return button_id

    def get_button(self, button_id: int) -> Optional[Dict[str, Any]]:
        """Get a ribbon button by ID."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, label, group_id, script_id, target_app, created_at
            FROM ribbon_buttons
            WHERE id = ?
        """, (button_id,))

        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None

    def get_all_buttons(self, group_id: Optional[int] = None,
                         target_app: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all ribbon buttons with bound script info."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if group_id:
            cursor.execute("""
                SELECT rb.id, rb.label, rb.group_id, rb.script_id, rb.target_app, rb.created_at,
                       ws.name as script_name, ws.main_function as script_function
                FROM ribbon_buttons rb
                LEFT JOIN wps_scripts ws ON rb.script_id = ws.id
                WHERE rb.group_id = ?
                ORDER BY rb.position, rb.label
            """, (group_id,))
        elif target_app:
            cursor.execute("""
                SELECT rb.id, rb.label, rb.group_id, rb.script_id, rb.target_app, rb.created_at,
                       ws.name as script_name, ws.main_function as script_function
                FROM ribbon_buttons rb
                LEFT JOIN wps_scripts ws ON rb.script_id = ws.id
                WHERE rb.target_app = ?
                ORDER BY rb.position, rb.label
            """, (target_app,))
        else:
            cursor.execute("""
                SELECT rb.id, rb.label, rb.group_id, rb.script_id, rb.target_app, rb.created_at,
                       ws.name as script_name, ws.main_function as script_function
                FROM ribbon_buttons rb
                LEFT JOIN wps_scripts ws ON rb.script_id = ws.id
                ORDER BY rb.position, rb.label
            """)

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def update_button(self, button_id: int, label: str) -> bool:
        """Update a ribbon button label."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("UPDATE ribbon_buttons SET label = ? WHERE id = ?", (label, button_id))
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()

        return success

    def bind_script(self, button_id: int, script_id: Optional[int]) -> bool:
        """Bind or unbind a script to a button.

        Args:
            button_id: The button ID.
            script_id: The script ID to bind, or None to unbind.

        Returns:
            True if binding updated successfully.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE ribbon_buttons SET script_id = ? WHERE id = ?
        """, (script_id, button_id))
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()

        return success

    def delete_button(self, button_id: int) -> bool:
        """Delete a ribbon button."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM ribbon_buttons WHERE id = ?", (button_id,))
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()

        return success

    def update_group_positions(self, tab_id: int, ordered_group_ids: list) -> None:
        """Update group positions after drag-and-drop reorder."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        for i, gid in enumerate(ordered_group_ids):
            cursor.execute(
                "UPDATE ribbon_groups SET position = ? WHERE id = ? AND tab_id = ?",
                (i, gid, tab_id)
            )
        conn.commit()
        conn.close()

    def update_button_positions(self, ordered_button_ids: list) -> None:
        """Update button positions after drag-and-drop reorder within a group."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        for i, bid in enumerate(ordered_button_ids):
            cursor.execute("UPDATE ribbon_buttons SET position = ? WHERE id = ?", (i, bid))
        conn.commit()
        conn.close()

    def move_button_to_group(self, button_id: int, new_group_id: int) -> bool:
        """Move a button to a different group."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE ribbon_buttons SET group_id = ? WHERE id = ?",
            (new_group_id, button_id)
        )
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success

    def get_button_with_script(self, button_id: int) -> Optional[Dict[str, Any]]:
        """Get a button with its bound script info."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT rb.id, rb.label, rb.group_id, rb.script_id, rb.target_app,
                   ws.name as script_name, ws.main_function as script_function
            FROM ribbon_buttons rb
            LEFT JOIN wps_scripts ws ON rb.script_id = ws.id
            WHERE rb.id = ?
        """, (button_id,))

        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None

    def get_full_ribbon_structure(self, target_app: str) -> List[Dict[str, Any]]:
        """Get complete ribbon structure for an app with buttons and scripts.

        Returns:
            List of tabs, each containing groups, each containing buttons with script info.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get tabs
        cursor.execute("""
            SELECT id, name FROM ribbon_tabs WHERE target_app = ? ORDER BY name
        """, (target_app,))
        tabs = [dict(row) for row in cursor.fetchall()]

        for tab in tabs:
            # Get groups for this tab
            cursor.execute("""
                SELECT id, name FROM ribbon_groups WHERE tab_id = ? ORDER BY position, name
            """, (tab['id'],))
            tab['groups'] = [dict(row) for row in cursor.fetchall()]

            for group in tab['groups']:
                # Get buttons for this group with script info
                cursor.execute("""
                    SELECT rb.id, rb.label, rb.script_id,
                           ws.name as script_name, ws.main_function as script_function
                    FROM ribbon_buttons rb
                    LEFT JOIN wps_scripts ws ON rb.script_id = ws.id
                    WHERE rb.group_id = ?
                    ORDER BY rb.position, rb.label
                """, (group['id'],))
                group['buttons'] = [dict(row) for row in cursor.fetchall()]

        conn.close()
        return tabs

    def generate_ribbon_xml(self, target_app: str) -> str:
        """Generate Ribbon XML from the structure tables.

        Args:
            target_app: Target application ('word' or 'excel').

        Returns:
            Ribbon XML string for WPS officeUI.
        """
        # Get full ribbon structure from new tables
        structure = self.get_full_ribbon_structure(target_app)

        if not structure:
            return '<mso:customUI xmlns:mso="http://schemas.microsoft.com/office/2009/07/customui"><mso:ribbon><mso:tabs/></mso:ribbon></mso:customUI>'

        # Build XML
        xml_parts = [
            '<mso:customUI xmlns:mso="http://schemas.microsoft.com/office/2009/07/customui">',
            '  <mso:ribbon>',
            '    <mso:tabs>'
        ]

        for tab in structure:
            tab_id = f"tab_{tab['id']}"
            xml_parts.append(f'      <mso:tab id="{xml_escape(tab_id)}" label="{xml_escape(tab["name"])}">')

            for group in tab.get('groups', []):
                group_id = f"group_{group['id']}"
                xml_parts.append(f'        <mso:group id="{xml_escape(group_id)}" label="{xml_escape(group["name"])}">')

                for button in group.get('buttons', []):
                    button_id = f"btn_{button['id']}"
                    btn_label = xml_escape(button["label"])
                    # Only generate action if button has bound script
                    if button.get('script_id') and button.get('script_name'):
                        script_name = xml_escape(button['script_name'])
                        xml_parts.append(
                            f'          <mso:button id="{xml_escape(button_id)}" '
                            f'idM="Project.Module1.{script_name}" '
                            f'label="{btn_label}" '
                            f'onAction="{script_name}" '
                            f'imageMso="ListMacros" />'
                        )
                    else:
                        # Button without script - just shows label, no action
                        xml_parts.append(
                            f'          <mso:button id="{xml_escape(button_id)}" '
                            f'label="{btn_label}" '
                            f'imageMso="ListMacros" />'
                        )

                xml_parts.append('        </mso:group>')

            xml_parts.append('      </mso:tab>')

        xml_parts.extend([
            '    </mso:tabs>',
            '  </mso:ribbon>',
            '</mso:customUI>'
        ])

        return '\n'.join(xml_parts)

    def get_bound_scripts(self, target_app: str) -> List[Dict[str, Any]]:
        """Get scripts that are bound to buttons for an app.

        Args:
            target_app: Target application ('word' or 'excel').

        Returns:
            List of scripts with their button binding info.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT ws.id, ws.name, ws.js_code, ws.main_function,
                   rb.label as button_label
            FROM ribbon_buttons rb
            JOIN wps_scripts ws ON rb.script_id = ws.id
            WHERE rb.target_app = ? AND rb.script_id IS NOT NULL
        """, (target_app,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def generate_js_code(self, target_app: str) -> str:
        """Generate JS macro code from bound scripts.

        Args:
            target_app: Target application ('word' or 'excel').

        Returns:
            Combined JS code for all bound scripts.
        """
        bound_scripts = self.get_bound_scripts(target_app)

        if not bound_scripts:
            return "// No scripts bound to buttons"

        # Combine all JS code
        js_parts = [
            "// WPS Script Manager - Auto-generated JS Macros",
            f"// Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"// Target: {target_app.upper()}",
            "",
        ]

        for script in bound_scripts:
            js_parts.append(f"// === {script['name']} (Button: {script.get('button_label', 'N/A')}) ===")
            js_code = script.get('js_code', '')
            if js_code:
                js_parts.append(js_code)
                js_parts.append("")
            else:
                js_parts.append("// No code content")
                js_parts.append("")

        return '\n'.join(js_parts)

    def generate_vba_module(self, target_app: str) -> str:
        """Generate VBA module code (deprecated - use generate_js_code for JS macros).

        Args:
            target_app: Target application ('word' or 'excel').

        Returns:
            VBA module code string (empty as we use JS now).
        """
        # This method is kept for backward compatibility but returns empty
        # as we now use JS macros, not VBA
        return ""

    def _create_ribbon_xml_file(self, zip_path: str, target_app: str) -> None:
        """Create and add ribbon XML to a zip file.

        Args:
            zip_path: Path to the zip file.
            target_app: Target application ('word' or 'excel').
        """
        xml_content = self.generate_ribbon_xml(target_app)

        with zipfile.ZipFile(zip_path, 'a', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr('customUI/customUI.xml', xml_content)

    def _create_vba_project(self, zip_path: str, target_app: str) -> None:
        """Create and add VBA project to a zip file.

        Args:
            zip_path: Path to the zip file.
            target_app: Target application ('word' or 'excel').
        """
        vba_code = self.generate_vba_module(target_app)

        # Create basic VBA project structure
        vba_project = f"""Attribute VB_Name = "ScriptManager"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False

{vba_code}
"""

        with zipfile.ZipFile(zip_path, 'a', zipfile.ZIP_DEFLATED) as zf:
            # VBA project structure
            zf.writestr('VBA/ScriptManager.bas', vba_project)

            # Project file
            project_content = f"""Microsoft Visual Basic for Applications Project
   Reference=*"{{00020813-0000-0000-C000-000000000046}}#1.9#0#SYSTEM32\\MSOUTLB.OLB#Microsoft Outlook 16.0 Object Library#0#0#0#0#1033#0"
   Module=ScriptManager, "ScriptManager.bas"
"""
            zf.writestr('project', project_content)

            # ThisDocument (for Word) or ThisWorkbook (for Excel)
            if target_app == "word":
                this_doc = """Attribute VB_Name = "ThisDocument"
' ThisDocument module for Word
Private Sub Document_Open()
    ScriptManager_Main
End Sub
"""
                zf.writestr('VBA/ThisDocument.bas', this_doc)
            else:
                this_doc = """Attribute VB_Name = "ThisWorkbook"
' ThisWorkbook module for Excel
Private Sub Workbook_Open()
    ScriptManager_Main
End Sub
"""
                zf.writestr('VBA/ThisWorkbook.bas', this_doc)

    def create_word_template(self) -> Optional[str]:
        """Create a Word template file (.dotm) with all Word scripts.

        Returns:
            Path to the created template file, or None if failed.
        """
        if not self.templates_dir:
            return None

        scripts = self.get_all_scripts("word")
        if not scripts:
            return None

        template_name = f"WpsScriptManager_Word_{datetime.now().strftime('%Y%m%d_%H%M%S')}.dotm"
        template_path = os.path.join(self.templates_dir, template_name)

        try:
            # Create a minimal .dotm file (it's a zip file)
            # First, create the necessary directory structure in memory

            # Create a basic Word document structure
            with zipfile.ZipFile(template_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                # [Content_Types].xml
                content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Default Extension="bin" ContentType="application/vnd.ms-word.document.macroEnabled.main"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.ms-word.document.macroEnabled.main+xml"/>
  <Override PartName="/_rels/.rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
</Types>
"""
                zf.writestr('[Content_Types].xml', content_types)

                # _rels/.rels
                rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.microsoft.com/office/2006/relationships/wordDocument" Target="word/document.xml"/>
</Relationships>
"""
                zf.writestr('_rels/.rels', rels)

                # word/document.xml
                document = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p>
      <w:r>
        <w:t>WPS Script Manager Template</w:t>
      </w:r>
    </w:p>
  </w:body>
</w:document>
"""
                zf.writestr('word/document.xml', document)

            # Now add the ribbon XML and VBA project
            self._create_ribbon_xml_file(template_path, "word")
            self._create_vba_project(template_path, "word")

            return template_path

        except Exception as e:
            print(f"Error creating Word template: {e}")
            return None

    def create_excel_template(self) -> Optional[str]:
        """Create an Excel template file (.xlam) with all Excel scripts.

        Returns:
            Path to the created template file, or None if failed.
        """
        if not self.templates_dir:
            return None

        scripts = self.get_all_scripts("excel")
        if not scripts:
            return None

        template_name = f"WpsScriptManager_Excel_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlam"
        template_path = os.path.join(self.templates_dir, template_name)

        try:
            # Create a minimal .xlam file (it's a zip file)
            with zipfile.ZipFile(template_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                # [Content_Types].xml
                content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>
"""
                zf.writestr('[Content_Types].xml', content_types)

                # _rels/.rels
                rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>
"""
                zf.writestr('_rels/.rels', rels)

                # xl/workbook.xml
                workbook = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheets>
    <sheet name="Sheet1" sheetId="1" r:id="rId1"/>
  </sheets>
</workbook>
"""
                zf.writestr('xl/workbook.xml', workbook)

                # xl/_rels/workbook.xml.rels
                workbook_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>
"""
                zf.writestr('xl/_rels/workbook.xml.rels', workbook_rels)

                # xl/worksheets/sheet1.xml
                worksheet = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetData/>
</worksheet>
"""
                zf.writestr('xl/worksheets/sheet1.xml', worksheet)

            # Now add the ribbon XML and VBA project
            self._create_ribbon_xml_file(template_path, "excel")
            self._create_vba_project(template_path, "excel")

            return template_path

        except Exception as e:
            print(f"Error creating Excel template: {e}")
            return None

    def deploy_all(self) -> bool:
        """Deploy all WPS templates to startup directories.

        Returns:
            True if deployment was successful, False otherwise.
        """
        if not self.templates_dir:
            return False

        # Check if there are any scripts
        all_scripts = self.get_all_scripts()
        if not all_scripts:
            return False

        try:
            # Create templates
            word_template = self.create_word_template()
            excel_template = self.create_excel_template()

            # Deploy to startup directories if paths are set
            deployed = False

            if word_template and self.word_startup:
                if os.path.exists(self.word_startup):
                    dest = os.path.join(self.word_startup, os.path.basename(word_template))
                    # Copy file
                    with open(word_template, 'rb') as src:
                        with open(dest, 'wb') as dst:
                            dst.write(src.read())
                    deployed = True

            if excel_template and self.excel_startup:
                if os.path.exists(self.excel_startup):
                    dest = os.path.join(self.excel_startup, os.path.basename(excel_template))
                    # Copy file
                    with open(excel_template, 'rb') as src:
                        with open(dest, 'wb') as dst:
                            dst.write(src.read())
                    deployed = True

            return deployed

        except Exception as e:
            print(f"Error deploying templates: {e}")
            return False
