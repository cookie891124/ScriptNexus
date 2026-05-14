"""JS script service for managing JavaScript bookmarks in Chrome."""

import os
import json
import sqlite3
import shutil
import subprocess
from datetime import datetime
from typing import Optional, List, Dict, Any


class JsService:
    """Service for managing JavaScript bookmarks with Chrome integration."""

    def __init__(self, db_path: str):
        """Initialize the JS service.

        Args:
            db_path: Path to the SQLite database file.
        """
        self.db_path = db_path
        self.chrome_path: Optional[str] = None
        self._init_db()

    def _init_db(self) -> None:
        """Initialize the database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS js_scripts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                parent_folder TEXT DEFAULT '',
                position INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    def set_chrome_path(self, path: str) -> None:
        """Set the Chrome bookmarks file path.

        Args:
            path: Path to the Chrome user data directory containing the Bookmarks file.
        """
        if path and path.strip() and not os.path.exists(path):
            os.makedirs(path)
        if path and path.strip():
            self.chrome_path = path

    def add_script(self, name: str, url: str, parent_folder: str = "",
                   position: int = 0) -> int:
        """Add a new JS script bookmark.

        Args:
            name: Script/bookmark name.
            url: URL for the bookmark.
            parent_folder: Parent folder name in bookmarks bar.
            position: Position in the folder.

        Returns:
            The ID of the newly created script.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO js_scripts (name, url, parent_folder, position)
            VALUES (?, ?, ?, ?)
        """, (name, url, parent_folder, position))

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
            SELECT id, name, url, parent_folder, position, created_at, updated_at
            FROM js_scripts
            WHERE id = ?
        """, (script_id,))

        row = cursor.fetchone()
        conn.close()

        if row is None:
            return None

        return dict(row)

    def get_all_scripts(self) -> List[Dict[str, Any]]:
        """Get all JS scripts.

        Returns:
            List of script data dictionaries.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, url, parent_folder, position, created_at, updated_at
            FROM js_scripts
            ORDER BY name
        """)

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def update_script(self, script_id: int, **kwargs) -> bool:
        """Update a script.

        Args:
            script_id: The script ID.
            **kwargs: Fields to update (name, url, parent_folder, position).

        Returns:
            True if updated successfully, False otherwise.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check if script exists
        cursor.execute("SELECT id FROM js_scripts WHERE id = ?", (script_id,))
        if cursor.fetchone() is None:
            conn.close()
            return False

        # Build update query
        allowed_fields = {"name", "url", "parent_folder", "position"}
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
        updates.append("updated_at = CURRENT_TIMESTAMP")

        query = f"""
            UPDATE js_scripts
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
        cursor.execute("SELECT id FROM js_scripts WHERE id = ?", (script_id,))
        if cursor.fetchone() is None:
            conn.close()
            return False

        cursor.execute("DELETE FROM js_scripts WHERE id = ?", (script_id,))
        conn.commit()
        conn.close()

        return True

    def generate_bookmarks_json(self) -> Dict[str, Any]:
        """Generate Chrome bookmarks JSON structure.

        Returns:
            Dictionary representing the Chrome bookmarks structure.
        """
        scripts = self.get_all_scripts()

        # Base bookmarks structure
        bookmarks = {
            "roots": {
                "bookmark_bar": {
                    "children": [],
                    "name": "Bookmarks bar",
                    "type": "other"
                },
                "other": {
                    "children": [],
                    "name": "Other bookmarks",
                    "type": "other"
                },
                "synced": {
                    "children": [],
                    "name": "Mobile bookmarks",
                    "type": "other"
                }
            },
            "version": 1
        }

        # Group scripts by parent_folder
        folders: Dict[str, List[Dict[str, Any]]] = {}
        for script in scripts:
            folder_name = script.get("parent_folder", "") or "JS Scripts"
            if folder_name not in folders:
                folders[folder_name] = []

            folders[folder_name].append({
                "id": str(script["id"]),
                "name": script["name"],
                "type": "url",
                "url": script["url"],
                "position": script.get("position", 0)
            })

        # Sort each folder by position
        for folder_name in folders:
            folders[folder_name].sort(key=lambda x: (x["position"], x["name"]))

        # Create folder structure in bookmark bar
        for folder_name, items in folders.items():
            if folder_name:
                # Create folder
                folder_node = {
                    "children": [
                        {
                            "date_added": datetime.now().isoformat(),
                            "id": item["id"],
                            "name": item["name"],
                            "type": "url",
                            "url": item["url"]
                        }
                        for item in items
                    ],
                    "date_added": datetime.now().isoformat(),
                    "date_modified": datetime.now().isoformat(),
                    "guid": folder_name,
                    "name": folder_name,
                    "type": "folder"
                }
                bookmarks["roots"]["bookmark_bar"]["children"].append(folder_node)
            else:
                # Add directly to bookmark bar
                for item in items:
                    bookmarks["roots"]["bookmark_bar"]["children"].append({
                        "date_added": datetime.now().isoformat(),
                        "id": item["id"],
                        "name": item["name"],
                        "type": "url",
                        "url": item["url"]
                    })

        return bookmarks

    def deploy_bookmarks(self) -> bool:
        """Deploy bookmarks to Chrome.

        Backs up existing bookmarks and writes new bookmarks.

        Returns:
            True if deployment was successful, False otherwise.
        """
        if not self.chrome_path:
            return False

        bookmarks_file = os.path.join(self.chrome_path, "Bookmarks")

        # Backup existing bookmarks if they exist
        if os.path.exists(bookmarks_file):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(self.chrome_path, f"Bookmarks.bak.{timestamp}")
            shutil.copy2(bookmarks_file, backup_file)

        # Generate new bookmarks
        bookmarks = self.generate_bookmarks_json()

        # Write bookmarks file
        try:
            with open(bookmarks_file, 'w', encoding='utf-8') as f:
                json.dump(bookmarks, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error deploying bookmarks: {e}")
            return False

    def open_in_chrome(self, script_id: int) -> bool:
        """Open a script URL in Chrome.

        Args:
            script_id: The script ID.

        Returns:
            True if successful, False otherwise.
        """
        script = self.get_script(script_id)
        if script is None:
            return False

        url = script["url"]

        try:
            # Try to open in Chrome using start command
            subprocess.Popen(
                f'start chrome "{url}"',
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return True
        except Exception as e:
            print(f"Error opening Chrome: {e}")
            return False
