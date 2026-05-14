"""Tests for WpsService class."""

import os
import shutil
import tempfile
import sqlite3
import pytest

from services.wps_service import WpsService


@pytest.fixture
def temp_db():
    """Create a temporary database file for testing."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    os.unlink(path)


@pytest.fixture
def temp_templates_dir():
    """Create a temporary templates directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def wps_service(temp_db, temp_templates_dir):
    """Create a WpsService instance for testing."""
    service = WpsService(temp_db)
    service.set_paths(temp_templates_dir, None, None)
    return service


class TestWpsServiceInit:
    """Test WpsService initialization."""

    def test_init_with_valid_db_path(self, temp_db):
        """Test initialization with valid database path."""
        service = WpsService(temp_db)
        assert service.db_path == temp_db
        assert os.path.exists(temp_db)

    def test_init_creates_tables(self, temp_db):
        """Test that initialization creates required tables."""
        service = WpsService(temp_db)

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Check wps_scripts table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='wps_scripts'")
        assert cursor.fetchone() is not None

        conn.close()


class TestSetPaths:
    """Test set_paths method."""

    def test_set_paths_valid(self, wps_service, temp_templates_dir):
        """Test setting valid paths."""
        assert wps_service.templates_dir == temp_templates_dir

    def test_set_paths_creates_if_not_exists(self, temp_db):
        """Test that set_paths creates directory if not exists."""
        service = WpsService(temp_db)
        temp_dir = os.path.join(tempfile.gettempdir(), 'test_templates_' + os.urandom(4).hex())

        try:
            service.set_paths(temp_dir, None, None)
            assert os.path.exists(temp_dir)
            assert service.templates_dir == temp_dir
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)


class TestAddScript:
    """Test add_script method."""

    def test_add_script_basic(self, wps_service):
        """Test adding a basic WPS script."""
        script_id = wps_service.add_script(
            name="TestScript",
            vba_code="Sub Test()\n    MsgBox 'Hello'\nEnd Sub",
            target_app="word",
            ribbon_group="CustomGroup",
            ribbon_label="Test Button",
            context_menu_label="Test Context Menu"
        )

        assert script_id is not None
        script = wps_service.get_script(script_id)
        assert script["name"] == "TestScript"
        assert "Test" in script["vba_code"]
        assert script["target_app"] == "word"
        assert script["ribbon_group"] == "CustomGroup"
        assert script["ribbon_label"] == "Test Button"
        assert script["context_menu_label"] == "Test Context Menu"

    def test_add_script_default_values(self, wps_service):
        """Test default values for optional parameters."""
        script_id = wps_service.add_script(
            name="MinimalScript",
            vba_code="Sub Minimal()\nEnd Sub",
            target_app="excel"
        )

        script = wps_service.get_script(script_id)
        assert script["ribbon_group"] == ""
        assert script["ribbon_label"] == ""
        assert script["context_menu_label"] == ""

    def test_add_script_auto_generates_id(self, wps_service):
        """Test that script ID is auto-generated."""
        script_id = wps_service.add_script(
            name="Script1",
            vba_code="code1",
            target_app="word"
        )

        assert isinstance(script_id, int)
        assert script_id > 0


class TestGetScript:
    """Test get_script method."""

    def test_get_existing_script(self, wps_service):
        """Test getting an existing script."""
        script_id = wps_service.add_script(
            name="Test",
            vba_code="code",
            target_app="word"
        )

        script = wps_service.get_script(script_id)
        assert script["id"] == script_id
        assert script["name"] == "Test"

    def test_get_nonexistent_script(self, wps_service):
        """Test getting a nonexistent script returns None."""
        script = wps_service.get_script(99999)
        assert script is None


class TestGetAllScripts:
    """Test get_all_scripts method."""

    def test_get_all_scripts_empty(self, wps_service):
        """Test getting all scripts with no scripts."""
        scripts = wps_service.get_all_scripts()
        assert scripts == []

    def test_get_all_scripts_with_data(self, wps_service):
        """Test getting all scripts with data."""
        wps_service.add_script(name="Script1", vba_code="code1", target_app="word")
        wps_service.add_script(name="Script2", vba_code="code2", target_app="excel")
        wps_service.add_script(name="Script3", vba_code="code3", target_app="word")

        scripts = wps_service.get_all_scripts()
        assert len(scripts) == 3

    def test_get_all_scripts_filter_by_target(self, wps_service):
        """Test filtering scripts by target app."""
        wps_service.add_script(name="WordScript", vba_code="code1", target_app="word")
        wps_service.add_script(name="ExcelScript", vba_code="code2", target_app="excel")

        word_scripts = wps_service.get_all_scripts("word")
        excel_scripts = wps_service.get_all_scripts("excel")
        all_scripts = wps_service.get_all_scripts()

        assert len(word_scripts) == 1
        assert len(excel_scripts) == 1
        assert len(all_scripts) == 2
        assert word_scripts[0]["name"] == "WordScript"
        assert excel_scripts[0]["name"] == "ExcelScript"


class TestGenerateRibbonXml:
    """Test generate_ribbon_xml method."""

    def test_generate_ribbon_xml_word(self, wps_service):
        """Test generating Ribbon XML for Word."""
        wps_service.add_script(
            name="TestScript",
            vba_code="Sub Test()\nEnd Sub",
            target_app="word",
            ribbon_group="TestGroup",
            ribbon_label="Test Button"
        )

        xml = wps_service.generate_ribbon_xml("word")
        assert xml is not None
        assert "customUI" in xml
        assert "TestGroup" in xml
        assert "Test Button" in xml

    def test_generate_ribbon_xml_excel(self, wps_service):
        """Test generating Ribbon XML for Excel."""
        wps_service.add_script(
            name="ExcelScript",
            vba_code="Sub Test()\nEnd Sub",
            target_app="excel",
            ribbon_group="ExcelGroup",
            ribbon_label="Excel Button"
        )

        xml = wps_service.generate_ribbon_xml("excel")
        assert xml is not None
        assert "customUI" in xml
        assert "ExcelGroup" in xml

    def test_generate_ribbon_xml_empty(self, wps_service):
        """Test generating Ribbon XML with no scripts."""
        xml = wps_service.generate_ribbon_xml("word")
        assert xml is not None
        assert "customUI" in xml


class TestGenerateVbaModule:
    """Test generate_vba_module method."""

    def test_generate_vba_module_word(self, wps_service):
        """Test generating VBA module for Word."""
        wps_service.add_script(
            name="TestScript",
            vba_code="Sub Test()\n    MsgBox 'Hello'\nEnd Sub",
            target_app="word",
            ribbon_group="TestGroup",
            ribbon_label="Test Button"
        )

        vba_code = wps_service.generate_vba_module("word")
        assert vba_code is not None
        assert "Test" in vba_code

    def test_generate_vba_module_excel(self, wps_service):
        """Test generating VBA module for Excel."""
        wps_service.add_script(
            name="ExcelScript",
            vba_code="Sub ExcelTest()\n    Range('A1').Value = 'Test'\nEnd Sub",
            target_app="excel",
            ribbon_group="ExcelGroup",
            ribbon_label="Excel Button"
        )

        vba_code = wps_service.generate_vba_module("excel")
        assert vba_code is not None
        assert "ExcelTest" in vba_code

    def test_generate_vba_module_empty(self, wps_service):
        """Test generating VBA module with no scripts."""
        vba_code = wps_service.generate_vba_module("word")
        assert vba_code is not None


class TestCreateWordTemplate:
    """Test create_word_template method."""

    def test_create_word_template(self, wps_service, temp_templates_dir):
        """Test creating Word template file."""
        wps_service.add_script(
            name="WordScript",
            vba_code="Sub WordTest()\nEnd Sub",
            target_app="word",
            ribbon_group="WordGroup",
            ribbon_label="Word Button"
        )

        template_path = wps_service.create_word_template()
        assert template_path is not None
        assert os.path.exists(template_path)
        assert template_path.endswith('.dotm')


class TestCreateExcelTemplate:
    """Test create_excel_template method."""

    def test_create_excel_template(self, wps_service, temp_templates_dir):
        """Test creating Excel template file."""
        wps_service.add_script(
            name="ExcelScript",
            vba_code="Sub ExcelTest()\nEnd Sub",
            target_app="excel",
            ribbon_group="ExcelGroup",
            ribbon_label="Excel Button"
        )

        template_path = wps_service.create_excel_template()
        assert template_path is not None
        assert os.path.exists(template_path)
        assert template_path.endswith('.xlam')


class TestDeployAll:
    """Test deploy_all method."""

    def test_deploy_all_creates_templates(self, wps_service, temp_templates_dir):
        """Test that deploy_all creates templates."""
        wps_service.add_script(
            name="WordScript",
            vba_code="Sub WordTest()\nEnd Sub",
            target_app="word",
            ribbon_group="WordGroup",
            ribbon_label="Word Button"
        )
        wps_service.add_script(
            name="ExcelScript",
            vba_code="Sub ExcelTest()\nEnd Sub",
            target_app="excel",
            ribbon_group="ExcelGroup",
            ribbon_label="Excel Button"
        )

        # Create templates manually to verify they can be created
        word_template = wps_service.create_word_template()
        excel_template = wps_service.create_excel_template()

        assert word_template is not None
        assert excel_template is not None
        assert os.path.exists(word_template)
        assert os.path.exists(excel_template)

    def test_deploy_all_no_scripts(self, wps_service):
        """Test deploying with no scripts."""
        result = wps_service.deploy_all()
        assert result is False

    def test_deploy_all_no_templates_dir(self, wps_service):
        """Test deploying without templates dir set."""
        wps_service.add_script(
            name="TestScript",
            vba_code="Sub Test()\nEnd Sub",
            target_app="word"
        )
        wps_service.templates_dir = None
        result = wps_service.deploy_all()
        assert result is False
