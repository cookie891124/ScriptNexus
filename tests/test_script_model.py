"""Tests for ScriptModel data model."""

import os
import tempfile
import pytest

from models.script_model import ScriptModel, ScriptType


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    os.unlink(path)


@pytest.fixture
def script_model(temp_db):
    """Create a ScriptModel instance for testing."""
    model = ScriptModel(temp_db)
    model.create_tables()
    yield model
    model.close()


class TestScriptType:
    """Test ScriptType enumeration."""

    def test_python_type(self):
        """Test PYTHON script type."""
        assert ScriptType.PYTHON.value == 'python'

    def test_wps_type(self):
        """Test WPS script type."""
        assert ScriptType.WPS.value == 'wps'

    def test_javascript_type(self):
        """Test JAVASCRIPT script type."""
        assert ScriptType.JAVASCRIPT.value == 'javascript'


class TestCreateTables:
    """Test create_tables method."""

    def test_create_tables_creates_all_tables(self, temp_db):
        """Test that create_tables creates all 5 tables."""
        model = ScriptModel(temp_db)
        model.create_tables()

        # Check all tables exist
        tables = model.query(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        table_names = [t['name'] for t in tables]

        assert 'scripts' in table_names
        assert 'dependencies' in table_names
        assert 'wps_mappings' in table_names
        assert 'js_bookmarks' in table_names
        assert 'config' in table_names

        model.close()


class TestScriptCRUD:
    """Test script CRUD operations."""

    def test_add_script(self, script_model):
        """Test add_script method."""
        script_id = script_model.add_script(
            name="test_script",
            script_type=ScriptType.PYTHON,
            code="print('hello')",
            description="A test script"
        )
        assert script_id is not None
        assert script_id > 0

    def test_add_script_with_parent(self, script_model):
        """Test add_script with parent_id."""
        parent_id = script_model.add_script(
            name="parent_script",
            script_type=ScriptType.PYTHON,
            code="print('parent')",
            description="Parent script"
        )

        child_id = script_model.add_script(
            name="child_script",
            script_type=ScriptType.PYTHON,
            code="print('child')",
            description="Child script",
            parent_id=parent_id
        )

        assert child_id is not None
        assert child_id > parent_id

    def test_get_script(self, script_model):
        """Test get_script method."""
        script_id = script_model.add_script(
            name="test_script",
            script_type=ScriptType.PYTHON,
            code="print('hello')",
            description="A test script"
        )

        script = script_model.get_script(script_id)
        assert script is not None
        assert script['id'] == script_id
        assert script['name'] == "test_script"
        assert script['script_type'] == 'python'
        assert script['code'] == "print('hello')"
        assert script['description'] == "A test script"

    def test_get_script_returns_none(self, script_model):
        """Test get_script returns None for non-existent script."""
        script = script_model.get_script(999)
        assert script is None

    def test_update_script(self, script_model):
        """Test update_script method."""
        script_id = script_model.add_script(
            name="test_script",
            script_type=ScriptType.PYTHON,
            code="print('hello')",
            description="A test script"
        )

        script_model.update_script(script_id, name="updated_script", description="Updated")

        script = script_model.get_script(script_id)
        assert script['name'] == "updated_script"
        assert script['description'] == "Updated"
        assert script['code'] == "print('hello')"  # Unchanged

    def test_update_script_multiple_fields(self, script_model):
        """Test update_script with multiple fields."""
        script_id = script_model.add_script(
            name="test_script",
            script_type=ScriptType.PYTHON,
            code="print('hello')",
            description="A test script"
        )

        script_model.update_script(
            script_id,
            name="new_name",
            code="print('world')",
            description="New description"
        )

        script = script_model.get_script(script_id)
        assert script['name'] == "new_name"
        assert script['code'] == "print('world')"
        assert script['description'] == "New description"

    def test_delete_script(self, script_model):
        """Test delete_script method."""
        script_id = script_model.add_script(
            name="test_script",
            script_type=ScriptType.PYTHON,
            code="print('hello')",
            description="A test script"
        )

        script_model.delete_script(script_id)

        script = script_model.get_script(script_id)
        assert script is None

    def test_delete_script_nonexistent(self, script_model):
        """Test delete_script with non-existent script."""
        # Should not raise an error
        script_model.delete_script(999)


class TestGetTree:
    """Test get_tree method for hierarchical script listing."""

    def test_get_tree_empty(self, script_model):
        """Test get_tree with no scripts."""
        tree = script_model.get_tree(ScriptType.PYTHON)
        assert tree == []

    def test_get_tree_flat_structure(self, script_model):
        """Test get_tree with scripts having no parent."""
        script_model.add_script(
            name="script1",
            script_type=ScriptType.PYTHON,
            code="code1",
            description="desc1"
        )
        script_model.add_script(
            name="script2",
            script_type=ScriptType.PYTHON,
            code="code2",
            description="desc2"
        )

        tree = script_model.get_tree(ScriptType.PYTHON)
        assert len(tree) == 2

    def test_get_tree_nested_structure(self, script_model):
        """Test get_tree with parent-child relationship."""
        parent_id = script_model.add_script(
            name="parent",
            script_type=ScriptType.PYTHON,
            code="parent_code",
            description="Parent script"
        )
        script_model.add_script(
            name="child1",
            script_type=ScriptType.PYTHON,
            code="child1_code",
            description="Child 1",
            parent_id=parent_id
        )
        script_model.add_script(
            name="child2",
            script_type=ScriptType.PYTHON,
            code="child2_code",
            description="Child 2",
            parent_id=parent_id
        )

        tree = script_model.get_tree(ScriptType.PYTHON)
        assert len(tree) == 1  # Only one root (parent)
        assert tree[0]['name'] == "parent"
        assert 'children' in tree[0]
        assert len(tree[0]['children']) == 2

    def test_get_tree_filters_by_type(self, script_model):
        """Test get_tree only returns scripts of specified type."""
        script_model.add_script(
            name="python_script",
            script_type=ScriptType.PYTHON,
            code="py_code",
            description="Python script"
        )
        script_model.add_script(
            name="wps_script",
            script_type=ScriptType.WPS,
            code="wps_code",
            description="WPS script"
        )

        python_tree = script_model.get_tree(ScriptType.PYTHON)
        wps_tree = script_model.get_tree(ScriptType.WPS)

        assert len(python_tree) == 1
        assert python_tree[0]['name'] == "python_script"
        assert len(wps_tree) == 1
        assert wps_tree[0]['name'] == "wps_script"


class TestConfig:
    """Test config CRUD operations."""

    def test_set_config(self, script_model):
        """Test set_config method."""
        script_model.set_config("test_key", "test_value")

    def test_get_config(self, script_model):
        """Test get_config method."""
        script_model.set_config("test_key", "test_value")

        value = script_model.get_config("test_key")
        assert value == "test_value"

    def test_get_config_with_default(self, script_model):
        """Test get_config returns default when key not found."""
        value = script_model.get_config("nonexistent", "default_value")
        assert value == "default_value"

    def test_get_config_without_default(self, script_model):
        """Test get_config returns None when key not found and no default."""
        value = script_model.get_config("nonexistent")
        assert value is None

    def test_update_config(self, script_model):
        """Test updating existing config."""
        script_model.set_config("key1", "value1")
        script_model.set_config("key1", "value2")

        value = script_model.get_config("key1")
        assert value == "value2"


class TestDependencies:
    """Test dependency operations."""

    def test_add_dependency(self, script_model):
        """Test add_dependency method."""
        script_id = script_model.add_script(
            name="test_script",
            script_type=ScriptType.PYTHON,
            code="code",
            description="Test"
        )

        dep_id = script_model.add_dependency(
            script_id=script_id,
            package_name="requests",
            version="2.28.0",
            installed=True
        )
        assert dep_id is not None
        assert dep_id > 0

    def test_get_dependencies(self, script_model):
        """Test get_dependencies method."""
        script_id = script_model.add_script(
            name="test_script",
            script_type=ScriptType.PYTHON,
            code="code",
            description="Test"
        )

        script_model.add_dependency(script_id, "requests", "2.28.0", True)
        script_model.add_dependency(script_id, "flask", "2.0.0", False)

        deps = script_model.get_dependencies(script_id)
        assert len(deps) == 2

        dep_names = [d['package_name'] for d in deps]
        assert "requests" in dep_names
        assert "flask" in dep_names

    def test_get_dependencies_empty(self, script_model):
        """Test get_dependencies with no dependencies."""
        script_id = script_model.add_script(
            name="test_script",
            script_type=ScriptType.PYTHON,
            code="code",
            description="Test"
        )

        deps = script_model.get_dependencies(script_id)
        assert len(deps) == 0

    def test_get_dependencies_for_nonexistent_script(self, script_model):
        """Test get_dependencies with non-existent script."""
        deps = script_model.get_dependencies(999)
        assert len(deps) == 0


class TestWpsMappings:
    """Test WPS mapping operations."""

    def test_add_wps_mapping(self, script_model):
        """Test add_wps_mapping method."""
        script_id = script_model.add_script(
            name="wps_script",
            script_type=ScriptType.WPS,
            code="code",
            description="WPS Test"
        )

        mapping_id = script_model.add_wps_mapping(
            script_id=script_id,
            ribbon_tab="Home",
            ribbon_group="Tools",
            button_label="Run Script",
            function_name="run_script"
        )
        assert mapping_id is not None
        assert mapping_id > 0

    def test_get_wps_mappings(self, script_model):
        """Test get_wps_mappings method."""
        script_id = script_model.add_script(
            name="wps_script",
            script_type=ScriptType.WPS,
            code="code",
            description="WPS Test"
        )

        script_model.add_wps_mapping(
            script_id, "Home", "Tools", "Button 1", "func1"
        )
        script_model.add_wps_mapping(
            script_id, "Insert", "Objects", "Button 2", "func2"
        )

        mappings = script_model.get_wps_mappings(script_id)
        assert len(mappings) == 2

    def test_get_wps_mappings_empty(self, script_model):
        """Test get_wps_mappings with no mappings."""
        script_id = script_model.add_script(
            name="wps_script",
            script_type=ScriptType.WPS,
            code="code",
            description="WPS Test"
        )

        mappings = script_model.get_wps_mappings(script_id)
        assert len(mappings) == 0

    def test_get_all_wps_scripts(self, script_model):
        """Test get_all_wps_scripts method."""
        script_id1 = script_model.add_script(
            name="wps_script1",
            script_type=ScriptType.WPS,
            code="code1",
            description="WPS Test 1"
        )
        script_id2 = script_model.add_script(
            name="wps_script2",
            script_type=ScriptType.WPS,
            code="code2",
            description="WPS Test 2"
        )

        script_model.add_wps_mapping(script_id1, "Home", "Tools", "Btn1", "func1")
        script_model.add_wps_mapping(script_id2, "Insert", "Objects", "Btn2", "func2")

        # Add a Python script (should not be included)
        script_model.add_script(
            name="python_script",
            script_type=ScriptType.PYTHON,
            code="py_code",
            description="Python Test"
        )

        wps_scripts = script_model.get_all_wps_scripts()
        assert len(wps_scripts) == 2


class TestJsBookmarks:
    """Test JS bookmark operations."""

    def test_add_js_bookmark(self, script_model):
        """Test add_js_bookmark method."""
        script_id = script_model.add_script(
            name="js_script",
            script_type=ScriptType.JAVASCRIPT,
            code="code",
            description="JS Test"
        )

        bookmark_id = script_model.add_js_bookmark(
            script_id=script_id,
            bookmark_name="My Bookmark",
            bookmark_url="https://example.com"
        )
        assert bookmark_id is not None
        assert bookmark_id > 0

    def test_get_js_bookmarks(self, script_model):
        """Test get_js_bookmarks method."""
        script_id = script_model.add_script(
            name="js_script",
            script_type=ScriptType.JAVASCRIPT,
            code="code",
            description="JS Test"
        )

        script_model.add_js_bookmark(
            script_id, "Bookmark 1", "https://example1.com"
        )
        script_model.add_js_bookmark(
            script_id, "Bookmark 2", "https://example2.com"
        )

        bookmarks = script_model.get_js_bookmarks(script_id)
        assert len(bookmarks) == 2

    def test_get_js_bookmarks_empty(self, script_model):
        """Test get_js_bookmarks with no bookmarks."""
        script_id = script_model.add_script(
            name="js_script",
            script_type=ScriptType.JAVASCRIPT,
            code="code",
            description="JS Test"
        )

        bookmarks = script_model.get_js_bookmarks(script_id)
        assert len(bookmarks) == 0

    def test_get_all_js_scripts(self, script_model):
        """Test get_all_js_scripts method."""
        script_id1 = script_model.add_script(
            name="js_script1",
            script_type=ScriptType.JAVASCRIPT,
            code="code1",
            description="JS Test 1"
        )
        script_id2 = script_model.add_script(
            name="js_script2",
            script_type=ScriptType.JAVASCRIPT,
            code="code2",
            description="JS Test 2"
        )

        script_model.add_js_bookmark(script_id1, "BM1", "https://url1.com")
        script_model.add_js_bookmark(script_id2, "BM2", "https://url2.com")

        # Add a Python script (should not be included)
        script_model.add_script(
            name="python_script",
            script_type=ScriptType.PYTHON,
            code="py_code",
            description="Python Test"
        )

        js_scripts = script_model.get_all_js_scripts()
        assert len(js_scripts) == 2
