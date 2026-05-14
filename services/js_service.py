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
        """Set the Chrome profile directory path.

        Args:
            path: Path to the Chrome profile directory (containing Bookmarks file).
        """
        if path and path.strip():
            self.chrome_path = path.strip()

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
        if not scripts:
            return {"roots": {"bookmark_bar": {"children": [], "name": "Bookmarks bar", "type": "folder"}}, "version": 1}

        now = datetime.now().isoformat()
        items = []
        for script in scripts:
            items.append({
                "date_added": now,
                "id": str(script["id"]),
                "name": script["name"],
                "type": "url",
                "url": script["url"],
            })

        # Sort by position then name
        items.sort(key=lambda x: (
            next((s.get("position", 0) for s in scripts if str(s["id"]) == x["id"]), 0),
            x["name"]
        ))

        bookmarks = {
            "roots": {
                "bookmark_bar": {
                    "children": items,
                    "name": "Bookmarks bar",
                    "type": "folder"
                }
            },
            "version": 1
        }
        return bookmarks

    def _read_existing_bookmarks(self) -> Optional[Dict[str, Any]]:
        """Read existing Chrome Bookmarks file.

        Returns:
            Parsed bookmarks dict, or None if file doesn't exist or is invalid.
        """
        bookmarks_file = os.path.join(self.chrome_path, "Bookmarks")
        if not os.path.exists(bookmarks_file):
            return None

        try:
            with open(bookmarks_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, PermissionError) as e:
            print(f"Error reading Chrome bookmarks: {e}")
            return None

    def _is_chrome_running(self) -> bool:
        """Check if Chrome is currently running (would lock Bookmarks file).

        Returns:
            True if Chrome process is detected.
        """
        try:
            import platform
            system = platform.system()
            if system == 'Windows':
                result = subprocess.run(
                    ['tasklist', '/FI', 'IMAGENAME eq chrome.exe'],
                    capture_output=True, text=True
                )
                return 'chrome.exe' in result.stdout.lower()
            elif system == 'Linux':
                result = subprocess.run(
                    ['pgrep', '-f', 'chrome'],
                    capture_output=True, text=True
                )
                return result.returncode == 0
            else:
                # macOS or unknown: skip detection
                return False
        except Exception:
            return False

    def deploy_bookmarks(self, target_folder: str = "JS Scripts") -> Dict[str, Any]:
        """Deploy bookmarks to Chrome with incremental merge.

        Reads existing Chrome Bookmarks, finds or creates target_folder
        in the bookmark bar, replaces only that folder's children with
        the managed bookmarks, preserves ALL other existing bookmarks.

        Args:
            target_folder: Name of the folder in Chrome bookmarks bar.

        Returns:
            Dict with 'success', 'message', and optional 'preview' keys.
        """
        if not self.chrome_path:
            return {"success": False, "message": "未设置 Chrome 书签路径"}

        # Check Chrome is not running (would lock file)
        if self._is_chrome_running():
            return {
                "success": False,
                "message": "请先关闭 Chrome 浏览器再部署书签\n（Chrome 运行时会锁定书签文件）"
            }

        bookmarks_file = os.path.join(self.chrome_path, "Bookmarks")
        scripts = self.get_all_scripts()

        # Read existing bookmarks or start fresh
        existing = self._read_existing_bookmarks()
        if existing is None:
            existing = {
                "roots": {
                    "bookmark_bar": {"children": [], "name": "Bookmarks bar", "type": "folder"},
                    "other": {"children": [], "name": "Other bookmarks", "type": "folder"},
                    "synced": {"children": [], "name": "Mobile bookmarks", "type": "folder"},
                },
                "version": 1
            }

        # Ensure bookmark_bar exists
        if "bookmark_bar" not in existing.get("roots", {}):
            existing["roots"]["bookmark_bar"] = {
                "children": [], "name": "Bookmarks bar", "type": "folder"
            }

        bookmark_bar = existing["roots"]["bookmark_bar"]
        if "children" not in bookmark_bar:
            bookmark_bar["children"] = []

        # Build managed bookmarks for the target folder
        now = datetime.now().isoformat()
        managed_items = []
        for script in scripts:
            managed_items.append({
                "date_added": now,
                "id": str(script["id"]),
                "name": script["name"],
                "type": "url",
                "url": script["url"],
            })

        # Find existing target folder or create one
        target_node = None
        for child in bookmark_bar["children"]:
            if child.get("name") == target_folder and child.get("type") == "folder":
                target_node = child
                break

        if target_node is None:
            # Create new folder node at the TOP of bookmark bar
            target_node = {
                "children": [],
                "date_added": now,
                "date_modified": now,
                "guid": target_folder,
                "name": target_folder,
                "type": "folder",
            }
            bookmark_bar["children"].insert(0, target_node)

        # Replace the folder's children with managed bookmarks
        target_node["children"] = managed_items
        target_node["date_modified"] = now

        # Backup existing before writing
        if os.path.exists(bookmarks_file):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(self.chrome_path, f"Bookmarks.bak.{timestamp}")
            try:
                shutil.copy2(bookmarks_file, backup_file)
            except Exception:
                pass

        # Write merged bookmarks
        try:
            with open(bookmarks_file, 'w', encoding='utf-8') as f:
                json.dump(existing, f, indent=2, ensure_ascii=False)

            # Build preview for UI display
            preview = json.dumps(existing, indent=2, ensure_ascii=False)

            return {
                "success": True,
                "message": f"已部署 {len(managed_items)} 个书签到文件夹「{target_folder}」\n\n请重启 Chrome 浏览器查看。",
                "preview": preview,
            }
        except PermissionError:
            return {"success": False, "message": "无法写入书签文件 — 请确认 Chrome 已关闭"}
        except Exception as e:
            return {"success": False, "message": f"部署失败: {e}"}

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
