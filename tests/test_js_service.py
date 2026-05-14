"""Tests for JsService class."""

import os
import json
import shutil
import tempfile
import sqlite3
import pytest

from services.js_service import JsService


@pytest.fixture
def temp_db():
    """Create a temporary database file for testing."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    os.unlink(path)


@pytest.fixture
def temp_bookmarks_dir():
    """Create a temporary bookmarks directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def js_service(temp_db, temp_bookmarks_dir):
    """Create a JsService instance for testing."""
    service = JsService(temp_db)
    service.set_chrome_path(temp_bookmarks_dir)
    return service


class TestJsServiceInit:
    """Test JsService initialization."""

    def test_init_with_valid_db_path(self, temp_db):
        """Test initialization with valid database path."""
        service = JsService(temp_db)
        assert service.db_path == temp_db
        assert os.path.exists(temp_db)

    def test_init_creates_tables(self, temp_db):
        """Test that initialization creates required tables."""
        service = JsService(temp_db)

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Check js_scripts table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='js_scripts'")
        assert cursor.fetchone() is not None

        conn.close()


class TestSetChromePath:
    """Test set_chrome_path method."""

    def test_set_chrome_path_valid(self, js_service, temp_bookmarks_dir):
        """Test setting valid chrome path."""
        js_service.set_chrome_path(temp_bookmarks_dir)
        assert js_service.chrome_path == temp_bookmarks_dir

    def test_set_chrome_path_creates_if_not_exists(self, temp_db):
        """Test that set_chrome_path creates directory if not exists."""
        service = JsService(temp_db)
        temp_dir = os.path.join(tempfile.gettempdir(), 'test_chrome_' + os.urandom(4).hex())

        try:
            service.set_chrome_path(temp_dir)
            assert os.path.exists(temp_dir)
            assert service.chrome_path == temp_dir
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)


class TestAddScript:
    """Test add_script method."""

    def test_add_script_basic(self, js_service):
        """Test adding a basic JS script."""
        script_id = js_service.add_script(
            name="TestScript",
            url="https://example.com/script",
            parent_folder="MyScripts",
            position=1
        )

        assert script_id is not None
        script = js_service.get_script(script_id)
        assert script["name"] == "TestScript"
        assert script["url"] == "https://example.com/script"
        assert script["parent_folder"] == "MyScripts"
        assert script["position"] == 1

    def test_add_script_default_values(self, js_service):
        """Test default values for optional parameters."""
        script_id = js_service.add_script(
            name="MinimalScript",
            url="https://example.com/min"
        )

        script = js_service.get_script(script_id)
        assert script["parent_folder"] == ""
        assert script["position"] == 0

    def test_add_script_auto_generates_id(self, js_service):
        """Test that script ID is auto-generated."""
        script_id = js_service.add_script(
            name="Script1",
            url="https://example.com/1"
        )

        assert isinstance(script_id, int)
        assert script_id > 0


class TestGetScript:
    """Test get_script method."""

    def test_get_existing_script(self, js_service):
        """Test getting an existing script."""
        script_id = js_service.add_script(
            name="Test",
            url="https://example.com/test"
        )

        script = js_service.get_script(script_id)
        assert script["id"] == script_id
        assert script["name"] == "Test"

    def test_get_nonexistent_script(self, js_service):
        """Test getting a nonexistent script returns None."""
        script = js_service.get_script(99999)
        assert script is None


class TestGetAllScripts:
    """Test get_all_scripts method."""

    def test_get_all_scripts_empty(self, js_service):
        """Test getting all scripts with no scripts."""
        scripts = js_service.get_all_scripts()
        assert scripts == []

    def test_get_all_scripts_with_data(self, js_service):
        """Test getting all scripts with data."""
        js_service.add_script(name="Script1", url="https://example.com/1")
        js_service.add_script(name="Script2", url="https://example.com/2")
        js_service.add_script(name="Script3", url="https://example.com/3")

        scripts = js_service.get_all_scripts()
        assert len(scripts) == 3

    def test_get_all_scripts_ordered_by_name(self, js_service):
        """Test that scripts are ordered by name."""
        js_service.add_script(name="Zebra", url="https://example.com/z")
        js_service.add_script(name="Alpha", url="https://example.com/a")
        js_service.add_script(name="Beta", url="https://example.com/b")

        scripts = js_service.get_all_scripts()
        assert len(scripts) == 3
        assert scripts[0]["name"] == "Alpha"
        assert scripts[1]["name"] == "Beta"
        assert scripts[2]["name"] == "Zebra"


class TestUpdateScript:
    """Test update_script method."""

    def test_update_script_url(self, js_service):
        """Test updating script URL."""
        script_id = js_service.add_script(
            name="Test",
            url="https://old.com/test"
        )

        js_service.update_script(script_id, url="https://new.com/test")

        script = js_service.get_script(script_id)
        assert script["url"] == "https://new.com/test"

    def test_update_script_folder(self, js_service):
        """Test updating script folder."""
        script_id = js_service.add_script(
            name="Test",
            url="https://example.com/test",
            parent_folder="OldFolder"
        )

        js_service.update_script(script_id, url="https://example.com/test", parent_folder="NewFolder")

        script = js_service.get_script(script_id)
        assert script["parent_folder"] == "NewFolder"

    def test_update_script_name(self, js_service):
        """Test updating script name."""
        script_id = js_service.add_script(
            name="OldName",
            url="https://example.com/test"
        )

        js_service.update_script(script_id, url="https://example.com/test", name="NewName")

        script = js_service.get_script(script_id)
        assert script["name"] == "NewName"

    def test_update_nonexistent_script(self, js_service):
        """Test updating nonexistent script returns False."""
        result = js_service.update_script(99999, url="https://example.com/test")
        assert result is False


class TestDeleteScript:
    """Test delete_script method."""

    def test_delete_script(self, js_service):
        """Test deleting a script."""
        script_id = js_service.add_script(
            name="Test",
            url="https://example.com/test"
        )

        result = js_service.delete_script(script_id)
        assert result is True

        script = js_service.get_script(script_id)
        assert script is None

    def test_delete_nonexistent_script(self, js_service):
        """Test deleting nonexistent script returns False."""
        result = js_service.delete_script(99999)
        assert result is False


class TestGenerateBookmarksJson:
    """Test generate_bookmarks_json method."""

    def test_generate_bookmarks_empty(self, js_service):
        """Test generating bookmarks JSON with no scripts."""
        bookmarks = js_service.generate_bookmarks_json()
        assert bookmarks is not None
        assert "roots" in bookmarks
        assert "bookmark_bar" in bookmarks["roots"]

    def test_generate_bookmarks_with_scripts(self, js_service):
        """Test generating bookmarks JSON with scripts."""
        js_service.add_script(
            name="TestScript",
            url="https://example.com/test",
            parent_folder="TestFolder",
            position=1
        )

        bookmarks = js_service.generate_bookmarks_json()
        assert bookmarks is not None

        # Check bookmark bar exists
        bookmark_bar = bookmarks["roots"]["bookmark_bar"]
        assert "children" in bookmark_bar

    def test_generate_bookmarks_structure(self, js_service):
        """Test bookmarks JSON has correct structure."""
        bookmarks = js_service.generate_bookmarks_json()

        # Verify root structure
        assert "roots" in bookmarks
        assert isinstance(bookmarks["roots"], dict)

        # Verify bookmark_bar structure
        bookmark_bar = bookmarks["roots"]["bookmark_bar"]
        assert "children" in bookmark_bar
        assert isinstance(bookmark_bar["children"], list)


class TestDeployBookmarks:
    """Test deploy_bookmarks method."""

    def test_deploy_bookmarks_creates_file(self, js_service, temp_bookmarks_dir):
        """Test that deploy_bookmarks creates the bookmarks file."""
        js_service.add_script(
            name="TestScript",
            url="https://example.com/test"
        )

        # Manually set the chrome path to our temp dir
        js_service.chrome_path = temp_bookmarks_dir

        # Get the expected bookmarks file path
        bookmarks_file = os.path.join(temp_bookmarks_dir, "Bookmarks")

        # Deploy bookmarks
        result = js_service.deploy_bookmarks()

        # Verify file was created
        assert os.path.exists(bookmarks_file)

    def test_deploy_bookmarks_backs_up_existing(self, js_service, temp_bookmarks_dir):
        """Test that deploy_bookmarks backs up existing bookmarks."""
        # Create an existing bookmarks file
        bookmarks_file = os.path.join(temp_bookmarks_dir, "Bookmarks")
        with open(bookmarks_file, 'w') as f:
            f.write('{"old": "data"}')

        js_service.add_script(
            name="TestScript",
            url="https://example.com/test"
        )

        # Deploy should create a backup
        result = js_service.deploy_bookmarks()

        # Check backup file exists (should have timestamp)
        backup_found = False
        for f in os.listdir(temp_bookmarks_dir):
            if f.startswith("Bookmarks.bak."):
                backup_found = True
                break

        assert backup_found

    def test_deploy_bookmarks_no_chrome_path(self, js_service):
        """Test deploying without chrome path set."""
        js_service.chrome_path = None
        result = js_service.deploy_bookmarks()
        assert result is False


class TestOpenInChrome:
    """Test open_in_chrome method."""

    def test_open_in_chrome_valid_script(self, js_service):
        """Test opening a valid script in Chrome."""
        script_id = js_service.add_script(
            name="TestScript",
            url="https://example.com/test"
        )

        # This should not raise an exception
        # Note: actual chrome opening may fail if Chrome is not installed
        result = js_service.open_in_chrome(script_id)
        # Returns True if script exists, regardless of whether Chrome opens
        assert result is True

    def test_open_in_chrome_nonexistent_script(self, js_service):
        """Test opening a nonexistent script returns False."""
        result = js_service.open_in_chrome(99999)
        assert result is False

    def test_open_in_chrome_with_url(self, js_service):
        """Test that open_in_chrome uses the script URL."""
        script_id = js_service.add_script(
            name="TestScript",
            url="https://example.com/test"
        )

        # Should return True for existing script
        result = js_service.open_in_chrome(script_id)
        assert result is True
