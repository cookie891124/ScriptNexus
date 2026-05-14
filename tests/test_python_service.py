"""Tests for PythonService class."""

import os
import shutil
import tempfile
import sqlite3
import pytest

from services.python_service import PythonService


@pytest.fixture
def temp_db():
    """Create a temporary database file for testing."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    os.unlink(path)


@pytest.fixture
def temp_scripts_dir():
    """Create a temporary scripts directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def python_service(temp_db, temp_scripts_dir):
    """Create a PythonService instance for testing."""
    service = PythonService(temp_db)
    service.set_scripts_dir(temp_scripts_dir)
    return service


class TestPythonServiceInit:
    """Test PythonService initialization."""

    def test_init_with_valid_db_path(self, temp_db):
        """Test initialization with valid database path."""
        service = PythonService(temp_db)
        assert service.db_path == temp_db
        assert os.path.exists(temp_db)

    def test_init_creates_tables(self, temp_db):
        """Test that initialization creates required tables."""
        service = PythonService(temp_db)

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Check scripts table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='scripts'")
        assert cursor.fetchone() is not None

        conn.close()


class TestSetScriptsDir:
    """Test set_scripts_dir method."""

    def test_set_scripts_dir_valid(self, python_service, temp_scripts_dir):
        """Test setting valid scripts directory."""
        python_service.set_scripts_dir(temp_scripts_dir)
        assert python_service.scripts_dir == temp_scripts_dir

    def test_set_scripts_dir_creates_if_not_exists(self, temp_db):
        """Test that set_scripts_dir creates directory if not exists."""
        service = PythonService(temp_db)
        temp_dir = os.path.join(tempfile.gettempdir(), 'test_scripts_' + os.urandom(4).hex())

        try:
            service.set_scripts_dir(temp_dir)
            assert os.path.exists(temp_dir)
            assert service.scripts_dir == temp_dir
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)


class TestAddScript:
    """Test add_script method."""

    def test_add_script_root_level(self, python_service):
        """Test adding a root level script."""
        script_id = python_service.add_script(
            name="test_script",
            code="print('hello')",
            description="Test script",
            parent_id=None
        )

        assert script_id is not None
        script = python_service.get_script(script_id)
        assert script["name"] == "test_script"
        assert script["code"] == "print('hello')"
        assert script["description"] == "Test script"
        assert script["parent_id"] is None

    def test_add_script_with_parent(self, python_service):
        """Test adding a script with parent."""
        parent_id = python_service.add_script(
            name="parent",
            code="# parent",
            description="Parent folder",
            parent_id=None
        )

        child_id = python_service.add_script(
            name="child",
            code="print('child')",
            description="Child script",
            parent_id=parent_id
        )

        child = python_service.get_script(child_id)
        assert child["parent_id"] == parent_id

    def test_add_script_auto_generates_id(self, python_service):
        """Test that script ID is auto-generated."""
        script_id = python_service.add_script(
            name="script1",
            code="code1",
            description="desc1"
        )

        assert isinstance(script_id, int)
        assert script_id > 0

    def test_add_script_default_values(self, python_service):
        """Test default values for optional parameters."""
        script_id = python_service.add_script(
            name="minimal_script",
            code="pass"
        )

        script = python_service.get_script(script_id)
        assert script["description"] == ""
        assert script["parent_id"] is None


class TestGetScript:
    """Test get_script method."""

    def test_get_existing_script(self, python_service):
        """Test getting an existing script."""
        script_id = python_service.add_script(
            name="test",
            code="code",
            description="desc"
        )

        script = python_service.get_script(script_id)
        assert script["id"] == script_id
        assert script["name"] == "test"

    def test_get_nonexistent_script(self, python_service):
        """Test getting a nonexistent script returns None."""
        script = python_service.get_script(99999)
        assert script is None


class TestGetTree:
    """Test get_tree method."""

    def test_get_tree_empty(self, python_service):
        """Test getting tree with no scripts."""
        tree = python_service.get_tree()
        assert tree == []

    def test_get_tree_single_root(self, python_service):
        """Test getting tree with single root script."""
        python_service.add_script(
            name="root",
            code="root_code",
            description="root_desc"
        )

        tree = python_service.get_tree()
        assert len(tree) == 1
        assert tree[0]["name"] == "root"
        assert "children" in tree[0]

    def test_get_tree_with_children(self, python_service):
        """Test getting tree with nested children."""
        parent_id = python_service.add_script(
            name="parent",
            code="# parent",
            description="Parent"
        )

        child1_id = python_service.add_script(
            name="child1",
            code="# child1",
            description="Child 1",
            parent_id=parent_id
        )

        child2_id = python_service.add_script(
            name="child2",
            code="# child2",
            description="Child 2",
            parent_id=parent_id
        )

        tree = python_service.get_tree()
        assert len(tree) == 1
        assert len(tree[0]["children"]) == 2
        child_names = [c["name"] for c in tree[0]["children"]]
        assert "child1" in child_names
        assert "child2" in child_names

    def test_get_tree_deep_nesting(self, python_service):
        """Test getting tree with deep nesting."""
        level1 = python_service.add_script(name="level1", code="#1")
        level2 = python_service.add_script(name="level2", code="#2", parent_id=level1)
        level3 = python_service.add_script(name="level3", code="#3", parent_id=level2)

        tree = python_service.get_tree()
        assert len(tree) == 1
        assert len(tree[0]["children"]) == 1
        assert len(tree[0]["children"][0]["children"]) == 1


class TestUpdateScript:
    """Test update_script method."""

    def test_update_script_code(self, python_service):
        """Test updating script code."""
        script_id = python_service.add_script(
            name="test",
            code="old_code",
            description="desc"
        )

        python_service.update_script(script_id, code="new_code")

        script = python_service.get_script(script_id)
        assert script["code"] == "new_code"
        assert script["description"] == "desc"

    def test_update_script_description(self, python_service):
        """Test updating script description."""
        script_id = python_service.add_script(
            name="test",
            code="code",
            description="old_desc"
        )

        python_service.update_script(script_id, code="code", description="new_desc")

        script = python_service.get_script(script_id)
        assert script["description"] == "new_desc"

    def test_update_script_name(self, python_service):
        """Test updating script name."""
        script_id = python_service.add_script(
            name="old_name",
            code="code"
        )

        python_service.update_script(script_id, code="code", name="new_name")

        script = python_service.get_script(script_id)
        assert script["name"] == "new_name"

    def test_update_nonexistent_script(self, python_service):
        """Test updating nonexistent script returns False."""
        result = python_service.update_script(99999, code="code")
        assert result is False


class TestDeleteScript:
    """Test delete_script method."""

    def test_delete_script(self, python_service):
        """Test deleting a script."""
        script_id = python_service.add_script(
            name="test",
            code="code"
        )

        result = python_service.delete_script(script_id)
        assert result is True

        script = python_service.get_script(script_id)
        assert script is None

    def test_delete_nonexistent_script(self, python_service):
        """Test deleting nonexistent script returns False."""
        result = python_service.delete_script(99999)
        assert result is False

    def test_delete_script_with_children(self, python_service):
        """Test deleting a script also deletes children."""
        parent_id = python_service.add_script(name="parent", code="#p")
        child_id = python_service.add_script(name="child", code="#c", parent_id=parent_id)

        python_service.delete_script(parent_id)

        assert python_service.get_script(parent_id) is None
        assert python_service.get_script(child_id) is None


class TestGetTreeStructure:
    """Test tree structure integrity."""

    def test_tree_node_has_required_fields(self, python_service):
        """Test that each tree node has required fields."""
        script_id = python_service.add_script(
            name="test",
            code="code",
            description="desc"
        )

        tree = python_service.get_tree()
        node = tree[0]

        assert "id" in node
        assert "name" in node
        assert "code" in node
        assert "description" in node
        assert "children" in node
        assert isinstance(node["children"], list)
