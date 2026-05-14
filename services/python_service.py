"""Python script service for managing Python scripts in the script manager."""

import os
import sqlite3
import subprocess
import time
from typing import Optional, List, Dict, Any


class PythonService:
    """Service for managing Python scripts with tree structure support."""

    def __init__(self, db_path: str):
        """Initialize the Python service.

        Args:
            db_path: Path to the SQLite database file.
        """
        self.db_path = db_path
        self.scripts_dir: Optional[str] = None
        self._init_db()

    def _init_db(self) -> None:
        """Initialize the database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create table with file_path column
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scripts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                script_type TEXT NOT NULL DEFAULT 'python',
                code TEXT NOT NULL,
                description TEXT DEFAULT '',
                file_path TEXT DEFAULT '',
                parent_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES scripts(id) ON DELETE CASCADE
            )
        """)

        # Check if file_path column exists, add it if not (for existing databases)
        cursor.execute("PRAGMA table_info(scripts)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'file_path' not in columns:
            cursor.execute("ALTER TABLE scripts ADD COLUMN file_path TEXT DEFAULT ''")

        conn.commit()
        conn.close()

    def set_scripts_dir(self, path: str) -> None:
        """Set the scripts storage directory.

        Args:
            path: Path to the scripts directory.
        """
        if not os.path.exists(path):
            os.makedirs(path)
        self.scripts_dir = path

    def sync_scripts_from_dir(self) -> int:
        """Sync Python scripts from the scripts directory to the database.

        Scans the scripts directory for .py files and adds them to the database
        if they don't already exist (by name). Updates file_path for existing scripts.

        Returns:
            Number of scripts synced (newly added).
        """
        if not self.scripts_dir or not os.path.exists(self.scripts_dir):
            return 0

        synced = 0
        updated = 0
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Walk through directory recursively
        for root, dirs, files in os.walk(self.scripts_dir):
            for filename in files:
                if filename.endswith('.py'):
                    filepath = os.path.join(root, filename)
                    script_name = os.path.splitext(filename)[0]

                    # Check if script already exists by name
                    cursor.execute("SELECT id, file_path FROM scripts WHERE name = ?", (script_name,))
                    row = cursor.fetchone()

                    if row is None:
                        # Read file content
                        try:
                            with open(filepath, 'r', encoding='utf-8') as f:
                                code = f.read()
                        except Exception:
                            continue

                        # Calculate relative path for description
                        rel_path = os.path.relpath(filepath, self.scripts_dir)
                        description = f"From file: {rel_path}"

                        # Insert into database with file_path
                        cursor.execute("""
                            INSERT INTO scripts (name, code, description, parent_id, script_type, file_path)
                            VALUES (?, ?, ?, NULL, 'python', ?)
                        """, (script_name, code, description, filepath))

                        synced += 1
                    else:
                        # Script exists - update file_path if empty or different
                        script_id = row[0]
                        existing_path = row[1] if row[1] else ""

                        # Update file_path if it's empty or the script was moved
                        if not existing_path or existing_path != filepath:
                            cursor.execute("""
                                UPDATE scripts
                                SET file_path = ?, updated_at = CURRENT_TIMESTAMP
                                WHERE id = ?
                            """, (filepath, script_id))
                            updated += 1

        conn.commit()
        conn.close()
        return synced

    def add_script(self, name: str, code: str, description: str = "",
                   parent_id: Optional[int] = None, file_path: str = "") -> int:
        """Add a new script.

        Args:
            name: Script name.
            code: Script code content.
            description: Script description.
            parent_id: Parent script/folder ID for tree structure.
            file_path: Path to the script file (for file sync).

        Returns:
            The ID of the newly created script.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO scripts (name, code, description, parent_id, script_type, file_path)
            VALUES (?, ?, ?, ?, 'python', ?)
        """, (name, code, description, parent_id, file_path))

        script_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # If file_path is provided, write the code to the file
        if file_path:
            self._write_script_to_file(file_path, code)
        elif self.scripts_dir:
            # Auto-generate file path if scripts_dir is set
            file_path = os.path.join(self.scripts_dir, f"{name}.py")
            self._write_script_to_file(file_path, code)
            # Update database with file path
            self.update_script(script_id, code=code, file_path=file_path)

        return script_id

    def _write_script_to_file(self, file_path: str, code: str) -> None:
        """Write script code to a file.

        Args:
            file_path: Path to the file.
            code: Script code to write.
        """
        # Ensure parent directory exists
        parent_dir = os.path.dirname(file_path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(code)

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
            SELECT id, name, code, description, file_path, parent_id, created_at, updated_at
            FROM scripts
            WHERE id = ?
        """, (script_id,))

        row = cursor.fetchone()
        conn.close()

        if row is None:
            return None

        return dict(row)

    def get_tree(self) -> List[Dict[str, Any]]:
        """Get the tree structure of all scripts.

        Returns:
            List of script nodes with children, representing the tree.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get all scripts
        cursor.execute("""
            SELECT id, name, code, description, file_path, parent_id, created_at, updated_at
            FROM scripts
            ORDER BY parent_id, name
        """)

        rows = cursor.fetchall()
        conn.close()

        # Build tree structure
        scripts_map = {}
        for row in rows:
            script = dict(row)
            script["children"] = []
            scripts_map[script["id"]] = script

        # Build the tree
        roots = []
        for script in scripts_map.values():
            if script["parent_id"] is None:
                roots.append(script)
            else:
                parent = scripts_map.get(script["parent_id"])
                if parent:
                    parent["children"].append(script)

        return roots

    def update_script(self, script_id: int, code: str, **kwargs) -> bool:
        """Update a script.

        Args:
            script_id: The script ID.
            code: New script code.
            **kwargs: Additional fields to update (name, description, parent_id, file_path).

        Returns:
            True if updated successfully, False otherwise.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check if script exists
        cursor.execute("SELECT id FROM scripts WHERE id = ?", (script_id,))
        if cursor.fetchone() is None:
            conn.close()
            return False

        # Get existing script data
        cursor.execute("SELECT file_path FROM scripts WHERE id = ?", (script_id,))
        file_path = cursor.fetchone()[0]

        # Build update query
        updates = ["code = ?", "updated_at = CURRENT_TIMESTAMP"]
        values = [code]

        for key, value in kwargs.items():
            if key in ("name", "description", "parent_id", "file_path"):
                updates.append(f"{key} = ?")
                values.append(value)

        values.append(script_id)

        query = f"""
            UPDATE scripts
            SET {", ".join(updates)}
            WHERE id = ?
        """

        cursor.execute(query, values)
        conn.commit()
        conn.close()

        # Write to file if file_path is set
        if file_path:
            self._write_script_to_file(file_path, code)

        return True

    def delete_script(self, script_id: int) -> bool:
        """Delete a script and all its children.

        Args:
            script_id: The script ID.

        Returns:
            True if deleted successfully, False otherwise.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check if script exists
        cursor.execute("SELECT id FROM scripts WHERE id = ?", (script_id,))
        if cursor.fetchone() is None:
            conn.close()
            return False

        # Get file path and name before deleting
        cursor.execute("SELECT file_path, name FROM scripts WHERE id = ?", (script_id,))
        row = cursor.fetchone()
        file_path = row[0] if row else ""
        script_name = row[1] if row else ""

        # First, recursively delete all children
        cursor.execute("SELECT id FROM scripts WHERE parent_id = ?", (script_id,))
        children = cursor.fetchall()
        for (child_id,) in children:
            self.delete_script(child_id)

        # Delete the script
        cursor.execute("DELETE FROM scripts WHERE id = ?", (script_id,))
        conn.commit()
        conn.close()

        # Delete the file if it exists
        # Try file_path first, then fall back to default locations
        files_to_try = []
        if file_path and file_path.strip():
            files_to_try.append(file_path)

        # If scripts_dir is set, search for the script file
        if script_name and self.scripts_dir:
            files_to_try.append(os.path.join(self.scripts_dir, f"{script_name}.py"))
            # Also check common subdirectories
            for subdir in ["python", "wps", "js"]:
                subdir_path = os.path.join(self.scripts_dir, subdir, f"{script_name}.py")
                files_to_try.append(subdir_path)
        elif script_name:
            # scripts_dir not set, search in common locations
            base_dir = os.path.dirname(self.db_path)
            for subdir in ["", "scripts", "scripts/python", "scripts/wps", "scripts/js"]:
                files_to_try.append(os.path.join(base_dir, subdir, f"{script_name}.py"))

        for fp in files_to_try:
            if fp and os.path.exists(fp):
                try:
                    os.remove(fp)
                except Exception:
                    pass  # Ignore file deletion errors

        return True

    def run_script(self, script_id: int, cwd: str = None, timeout: int = 60, thread=None) -> Dict[str, Any]:
        """Run a script via PowerShell.

        Args:
            script_id: The script ID.
            cwd: Working directory for script execution. If None, uses scripts_dir.
            timeout: Timeout in seconds (default 60s for long-running scripts).
            thread: ScriptRunnerThread instance for process reference (optional)

        Returns:
            Dictionary with success status, output, and error.
        """
        script = self.get_script(script_id)
        if script is None:
            return {
                "success": False,
                "output": "",
                "error": f"Script {script_id} not found"
            }

        # Determine working directory
        # Use scripts_dir as working directory so relative paths like config.json work
        working_dir = cwd if cwd else self.scripts_dir

        # Create temporary Python file IN the scripts directory (not temp)
        # This ensures __file__ points to the correct directory
        if not os.path.exists(working_dir):
            os.makedirs(working_dir, exist_ok=True)

        temp_filename = f"_temp_script_{script_id}_{int(time.time() * 1000)}.py"
        temp_path = os.path.join(working_dir, temp_filename)

        try:
            # Write script to temp file in scripts directory
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write(script["code"])

            # Run via PowerShell with working directory set to scripts_dir
            ps_command = f'python "{temp_path}"'
            process = subprocess.Popen(
                ps_command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=working_dir
            )

            # Store process reference in thread for stopping
            if thread:
                thread.process = process

            try:
                stdout, stderr = process.communicate(timeout=timeout)
                return {
                    "success": process.returncode == 0,
                    "output": stdout,
                    "error": stderr
                }
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate()
                return {
                    "success": False,
                    "output": "",
                    "error": f"Script execution timed out ({timeout}s)"
                }

        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e)
            }
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def prepare_script_for_execution(self, script_id: int) -> Optional[dict]:
        """Prepare script file for execution by QProcess.

        Returns the original file_path when available (so sibling modules
        like db_utils.py are importable), falling back to a temp file
        for scripts created directly in the editor.

        Args:
            script_id: The script ID.

        Returns:
            Dict with keys 'path', 'is_temp', 'script_dir', or None if not found.
        """
        script = self.get_script(script_id)
        if script is None:
            return None

        # If the script has a real file_path that exists, use it directly.
        # This ensures __file__ and sys.path point to the original directory,
        # making sibling modules (e.g. db_utils.py) importable.
        file_path = script.get("file_path", "")
        if file_path and os.path.exists(file_path):
            return {
                "path": file_path,
                "is_temp": False,
                "script_dir": os.path.dirname(file_path),
            }

        # Fallback: create a temp file for scripts without a disk file
        working_dir = self.scripts_dir or os.path.dirname(self.db_path)
        if not os.path.exists(working_dir):
            os.makedirs(working_dir, exist_ok=True)

        temp_filename = f"_temp_script_{script_id}_{int(time.time() * 1000)}.py"
        temp_path = os.path.join(working_dir, temp_filename)

        with open(temp_path, 'w', encoding='utf-8') as f:
            f.write(script["code"])

        return {
            "path": temp_path,
            "is_temp": True,
            "script_dir": working_dir,
        }

    def get_working_directory(self) -> str:
        """Get the working directory for script execution.

        Returns:
            The scripts directory path, or database directory if not set.
        """
        return self.scripts_dir or os.path.dirname(self.db_path)
