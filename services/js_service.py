"""JS script service for managing JavaScript bookmarks in Chrome."""

import os
import json
import re
import uuid
import sqlite3
import shutil
import subprocess
from datetime import datetime
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse

ALLOWED_URL_SCHEMES = {'http', 'https', 'javascript', 'file'}

def validate_url(url: str) -> bool:
    """Return True if url uses an allowed scheme."""
    if not url:
        return False
    parsed = urlparse(url)
    return parsed.scheme in ALLOWED_URL_SCHEMES


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
                description TEXT DEFAULT '',
                parent_folder TEXT DEFAULT '',
                position INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Migrate: add description column if missing (for existing databases)
        try:
            cursor.execute("SELECT description FROM js_scripts LIMIT 0")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE js_scripts ADD COLUMN description TEXT DEFAULT ''")

        conn.commit()
        conn.close()

    def set_chrome_path(self, path: str) -> None:
        """Set the Chrome profile directory or Bookmarks file path.

        Args:
            path: Path to the Chrome profile directory or Bookmarks file.
        """
        if path and path.strip():
            self.chrome_path = path.strip()

    def _get_bookmarks_file(self) -> Optional[str]:
        """Get the actual Bookmarks file path.

        Handles both cases: chrome_path as a directory (appends 'Bookmarks')
        or as the file itself.

        Returns:
            Full path to Bookmarks file, or None if chrome_path is not set.
        """
        if not self.chrome_path:
            return None
        if os.path.basename(self.chrome_path) == "Bookmarks":
            return self.chrome_path
        return os.path.join(self.chrome_path, "Bookmarks")

    def add_script(self, name: str, url: str, parent_folder: str = "",
                   position: int = 0, description: str = "") -> int:
        """Add a new JS script bookmark."""
        if url and not validate_url(url):
            raise ValueError(f"不支持的 URL 协议: {url[:80]}...\n仅支持 http / https / javascript / file 协议。")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("""
            INSERT INTO js_scripts (name, url, description, parent_folder, position, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, url, description, parent_folder, position, now, now))

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
            SELECT id, name, url, description, parent_folder, position, created_at, updated_at
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
            SELECT id, name, url, description, parent_folder, position, created_at, updated_at
            FROM js_scripts
            ORDER BY parent_folder, position, name
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
        allowed_fields = {"name", "url", "description", "parent_folder", "position"}
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
        bookmarks_file = self._get_bookmarks_file()
        if not bookmarks_file or not os.path.exists(bookmarks_file):
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
        """Deploy bookmarks to Chrome -- clean-slate replacement approach.

        Replaces the entire content of the target folder with fresh entries
        built from the scripts database.  Deterministic UUID v5 GUIDs ensure
        Chrome Sync recognises the same script across deploys.  Only user-
        created subfolders (whose names don't collide with managed subfolders)
        are preserved.

        This "replace, don't merge" design makes duplicates structurally
        impossible: every managed script produces exactly one entry, and
        the old folder contents are discarded before the new list is written.

        Args:
            target_folder: Name of the folder in Chrome bookmarks bar.

        Returns:
            Dict with 'success', 'message' keys.
        """
        if not self.chrome_path:
            return {"success": False, "message": "未设置 Chrome 书签路径"}

        if self._is_chrome_running():
            return {
                "success": False,
                "message": "请先关闭 Chrome 浏览器再部署书签\n（Chrome 运行时会锁定书签文件）"
            }

        bookmarks_file = self._get_bookmarks_file()
        if not bookmarks_file:
            return {"success": False, "message": "无法确定 Chrome 书签文件路径"}
        scripts = self.get_all_scripts()

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

        bookmark_bar = existing.setdefault("roots", {}).setdefault(
            "bookmark_bar", {"children": [], "name": "Bookmarks bar", "type": "folder"})
        bookmark_bar.setdefault("children", [])

        now = datetime.now().isoformat()

        # ---- Find / create root folder ----
        root_node = None
        for child in bookmark_bar["children"]:
            if child.get("name") == target_folder and child.get("type") == "folder":
                root_node = child
                break

        if root_node is None:
            root_node = {
                "children": [],
                "date_added": now,
                "guid": "snx-root-" + target_folder,
                "name": target_folder,
                "type": "folder",
            }
            bookmark_bar["children"].insert(0, root_node)

        # ---- Build brand-new entries for every managed script ----
        _SNX_NS = uuid.UUID('a3f1b8c0-5e4d-7f6a-9b2c-1d3e5f7a8b9c')

        root_entries = []
        subfolder_entries: Dict[str, list] = {}
        for script in scripts:
            guid = str(uuid.uuid5(_SNX_NS, f"scriptnexus-js-{script['id']}"))
            entry = {
                "date_added": script.get("created_at", now),
                "date_modified": script.get("updated_at", now),
                "guid": guid,
                "id": str(script["id"]),
                "name": script["name"],
                "type": "url",
                "url": script["url"],
            }
            sub = script.get("parent_folder", "").strip()
            if sub:
                subfolder_entries.setdefault(sub, []).append(entry)
            else:
                root_entries.append(entry)

        # ---- Assemble new children list (replace, not merge) ----
        new_children: list = list(root_entries)

        # Managed subfolders
        for sub_name, items in subfolder_entries.items():
            new_children.append({
                "children": items,
                "date_added": now,
                "date_modified": now,
                "guid": f"{target_folder}/{sub_name}",
                "name": sub_name,
                "type": "folder",
            })

        # Preserve user-created subfolders that don't collide with managed ones
        for child in list(root_node.get("children", [])):
            if child.get("type") == "folder" and \
               child.get("name", "") not in subfolder_entries:
                new_children.append(child)

        # Replace folder contents entirely -- old url entries are discarded
        root_node["children"] = new_children
        root_node["date_modified"] = now

        # Strip sync metadata so Chrome does a clean re-sync with our GUIDs
        existing.pop("sync_metadata", None)
        existing.pop("checksum", None)

        # ---- Write ----
        bookmarks_dir = os.path.dirname(bookmarks_file)

        if os.path.exists(bookmarks_file):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            try:
                shutil.copy2(bookmarks_file,
                             os.path.join(bookmarks_dir, f"Bookmarks.bak.{timestamp}"))
            except Exception:
                pass

        # Delete journal files so Chrome doesn't replay stale changes
        for jname in ("Bookmarks.journal", "Bookmarks-wal", "Bookmarks.shm"):
            jpath = os.path.join(bookmarks_dir, jname)
            try:
                os.remove(jpath)
            except OSError:
                pass

        try:
            with open(bookmarks_file, 'w', encoding='utf-8') as f:
                json.dump(existing, f, indent=2, ensure_ascii=False)

            bak_path = os.path.join(bookmarks_dir, "Bookmarks.bak")
            try:
                shutil.copy2(bookmarks_file, bak_path)
            except Exception:
                pass

            return {
                "success": True,
                "message": f"已部署 {len(scripts)} 个书签到文件夹「{target_folder}」\n\n请重启 Chrome 浏览器查看。",
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
            os.startfile(url)
            return True
        except Exception as e:
            print(f"Error opening Chrome: {e}")
            return False
