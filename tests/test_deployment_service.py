"""Tests for DeploymentService class."""

import os
import shutil
import tempfile
import zipfile
from unittest.mock import patch, MagicMock
import pytest

from core.deployment_service import DeploymentService
from services.wps_service import WpsService
from services.js_service import JsService


def create_mock_template(template_path: str, app_type: str):
    """Helper to create a mock template file with proper structure."""
    with zipfile.ZipFile(template_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        if app_type == 'word':
            # Word .dotm structure
            zf.writestr('[Content_Types].xml', '''<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
    <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
    <Override PartName="/word/document.xml" ContentType="application/vnd.ms-word.document.macroEnabled.main+xml"/>
    <Override PartName="/word/vbaProject.bin" ContentType="application/vnd.ms-office.vbaProject"/>
</Types>''')
            zf.writestr('word/document.xml', '''<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body><w:p><w:r><w:t>WPS Script Manager Template</w:t></w:r></w:p>
</w:body></w:document>''')
            zf.writestr('word/vbaProject.bin', b'MOCK_VBA_PROJECT_BINARY_DATA')
            zf.writestr('word/customUI/customUI.xml', '''<?xml version="1.0" encoding="utf-8"?>
<customUI xmlns="http://schemas.microsoft.com/office/2009/07/customui">
  <ribbon>
    <tabs>
      <tab id="WpsScriptManagerTab" label="脚本管理器" insertAfterMso="TabHome">
        <groups>
          <group id="Group_Test" label="Test Group">
            <button id="Btn_TestScript" label="Test Button" size="large" onAction="OnAction_TestScript" />
          </group>
        </groups>
      </tab>
    </tabs>
  </ribbon>
</customUI>''')
        else:
            # Excel .xlam structure
            zf.writestr('[Content_Types].xml', '''<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
    <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
    <Override PartName="/xl/workbook.xml" ContentType="application/vnd.ms-excel.sheet.macroEnabled.main+xml"/>
    <Override PartName="/xl/vbaProject.bin" ContentType="application/vnd.ms-office.vbaProject"/>
</Types>''')
            zf.writestr('xl/workbook.xml', '''<?xml version="1.0" encoding="UTF-8"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
    <sheets><sheet name="Sheet1" sheetId="1"/></sheets>
</workbook>''')
            zf.writestr('xl/vbaProject.bin', b'MOCK_VBA_PROJECT_BINARY_DATA')
            zf.writestr('xl/customUI/customUI.xml', '''<?xml version="1.0" encoding="utf-8"?>
<customUI xmlns="http://schemas.microsoft.com/office/2009/07/customui">
  <ribbon>
    <tabs>
      <tab id="WpsScriptManagerTab" label="脚本管理器" insertAfterMso="TabHome">
        <groups>
          <group id="Group_Test" label="Test Group">
            <button id="Btn_TestScript" label="Test Button" size="large" onAction="OnAction_TestScript" />
          </group>
        </groups>
      </tab>
    </tabs>
  </ribbon>
</customUI>''')


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
def temp_bookmarks_dir():
    """Create a temporary bookmarks directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def deployment_service(temp_db, temp_templates_dir, temp_bookmarks_dir):
    """Create a DeploymentService instance for testing."""
    wps_service = WpsService(temp_db)
    wps_service.set_paths(temp_templates_dir, None, None)

    js_service = JsService(temp_db)
    js_service.set_chrome_path(temp_bookmarks_dir)

    return DeploymentService(wps_service, js_service)


class TestDeploymentServiceInit:
    """Test DeploymentService initialization."""

    def test_init_with_valid_services(self, temp_db, temp_templates_dir, temp_bookmarks_dir):
        """Test initialization with valid service instances."""
        wps_service = WpsService(temp_db)
        wps_service.set_paths(temp_templates_dir, None, None)

        js_service = JsService(temp_db)
        js_service.set_chrome_path(temp_bookmarks_dir)

        service = DeploymentService(wps_service, js_service)
        assert service.wps_service == wps_service
        assert service.js_service == js_service


class TestDeployAll:
    """Test deploy_all method."""

    @patch('core.deployment_service.DeploymentService._deploy_word_template_com')
    @patch('core.deployment_service.DeploymentService._deploy_excel_template_com')
    def test_deploy_all_success(self, mock_excel_com, mock_word_com, deployment_service, temp_db, temp_templates_dir):
        """Test successful deployment of all components."""
        # Mock COM methods to create template files
        def mock_word_com_impl(scripts, template_path):
            create_mock_template(template_path, 'word')
            return {"success": True, "deployed": True, "message": "Word template created"}

        def mock_excel_com_impl(scripts, template_path):
            create_mock_template(template_path, 'excel')
            return {"success": True, "deployed": True, "message": "Excel template created"}

        mock_word_com.side_effect = mock_word_com_impl
        mock_excel_com.side_effect = mock_excel_com_impl

        # Add WPS scripts for both Word and Excel
        deployment_service.wps_service.add_script(
            name="WordScript",
            vba_code="Sub WordTest()\nEnd Sub",
            target_app="word",
            ribbon_group="WordGroup",
            ribbon_label="Word Button"
        )
        deployment_service.wps_service.add_script(
            name="ExcelScript",
            vba_code="Sub ExcelTest()\nEnd Sub",
            target_app="excel",
            ribbon_group="ExcelGroup",
            ribbon_label="Excel Button"
        )

        # Add JS script for Chrome bookmarks
        deployment_service.js_service.add_script(
            name="TestScript",
            url="https://example.com/test"
        )

        result = deployment_service.deploy_all()

        assert result['success'] is True
        assert result['wps_word'] is True
        assert result['wps_excel'] is True
        assert result['chrome_bookmarks'] is True
        assert result['errors'] == []

    @patch('core.deployment_service.DeploymentService._deploy_word_template_com')
    @patch('core.deployment_service.DeploymentService._deploy_excel_template_com')
    def test_deploy_all_partial_failure_no_js_scripts(self, mock_excel_com, mock_word_com, deployment_service, temp_db, temp_templates_dir):
        """Test deployment with no JS scripts - should still succeed, just no bookmarks."""
        # Mock COM methods to create template files
        def mock_word_com_impl(scripts, template_path):
            create_mock_template(template_path, 'word')
            return {"success": True, "deployed": True, "message": "Word template created"}

        def mock_excel_com_impl(scripts, template_path):
            create_mock_template(template_path, 'excel')
            return {"success": True, "deployed": True, "message": "Excel template created"}

        mock_word_com.side_effect = mock_word_com_impl
        mock_excel_com.side_effect = mock_excel_com_impl

        # Add WPS scripts
        deployment_service.wps_service.add_script(
            name="WordScript",
            vba_code="Sub WordTest()\nEnd Sub",
            target_app="word",
            ribbon_group="WordGroup",
            ribbon_label="Word Button"
        )
        deployment_service.wps_service.add_script(
            name="ExcelScript",
            vba_code="Sub ExcelTest()\nEnd Sub",
            target_app="excel",
            ribbon_group="ExcelGroup",
            ribbon_label="Excel Button"
        )

        result = deployment_service.deploy_all()

        # No JS scripts means deploy_bookmarks still succeeds (writes empty bookmarks)
        assert result['success'] is True
        assert result['wps_word'] is True
        assert result['wps_excel'] is True
        assert result['chrome_bookmarks'] is True
        assert result['errors'] == []

    def test_deploy_all_partial_failure_no_wps_scripts(self, deployment_service, temp_db):
        """Test deployment with no WPS scripts - should still succeed with just bookmarks."""
        # Add JS script only
        deployment_service.js_service.add_script(
            name="TestScript",
            url="https://example.com/test"
        )

        result = deployment_service.deploy_all()

        # No WPS scripts means templates return None, but that's not an error
        assert result['success'] is True
        assert result['wps_word'] is False
        assert result['wps_excel'] is False
        assert result['chrome_bookmarks'] is True

    def test_deploy_all_no_scripts_at_all(self, deployment_service):
        """Test deployment with no scripts at all."""
        result = deployment_service.deploy_all()

        # No scripts means nothing to deploy, but not an error
        assert result['success'] is True
        assert result['wps_word'] is False
        assert result['wps_excel'] is False
        assert result['chrome_bookmarks'] is True

    @patch('core.deployment_service.DeploymentService._deploy_word_template_com')
    def test_deploy_all_wps_word_only(self, mock_word_com, deployment_service, temp_db, temp_templates_dir):
        """Test deployment with only Word scripts."""
        def mock_word_com_impl(scripts, template_path):
            create_mock_template(template_path, 'word')
            return {"success": True, "deployed": True, "message": "Word template created"}

        mock_word_com.side_effect = mock_word_com_impl

        deployment_service.wps_service.add_script(
            name="WordScript",
            vba_code="Sub WordTest()\nEnd Sub",
            target_app="word",
            ribbon_group="WordGroup",
            ribbon_label="Word Button"
        )
        deployment_service.js_service.add_script(
            name="TestScript",
            url="https://example.com/test"
        )

        result = deployment_service.deploy_all()

        assert result['success'] is True
        assert result['wps_word'] is True
        assert result['wps_excel'] is False
        assert result['chrome_bookmarks'] is True

    @patch('core.deployment_service.DeploymentService._deploy_excel_template_com')
    def test_deploy_all_wps_excel_only(self, mock_excel_com, deployment_service, temp_db, temp_templates_dir):
        """Test deployment with only Excel scripts."""
        def mock_excel_com_impl(scripts, template_path):
            create_mock_template(template_path, 'excel')
            return {"success": True, "deployed": True, "message": "Excel template created"}

        mock_excel_com.side_effect = mock_excel_com_impl

        deployment_service.wps_service.add_script(
            name="ExcelScript",
            vba_code="Sub ExcelTest()\nEnd Sub",
            target_app="excel",
            ribbon_group="ExcelGroup",
            ribbon_label="Excel Button"
        )
        deployment_service.js_service.add_script(
            name="TestScript",
            url="https://example.com/test"
        )

        result = deployment_service.deploy_all()

        assert result['success'] is True
        assert result['wps_word'] is False
        assert result['wps_excel'] is True
        assert result['chrome_bookmarks'] is True

    def test_deploy_all_no_templates_dir(self, temp_db, temp_bookmarks_dir):
        """Test deployment without templates directory set."""
        wps_service = WpsService(temp_db)
        # Don't set templates dir, only word_startup
        wps_service.word_startup = None
        wps_service.excel_startup = None

        js_service = JsService(temp_db)
        js_service.set_chrome_path(temp_bookmarks_dir)

        service = DeploymentService(wps_service, js_service)
        result = service.deploy_all()

        # No templates dir means WPS templates return message but not error
        assert result['success'] is True
        assert result['wps_word'] is False
        assert result['wps_excel'] is False

    def test_deploy_all_no_chrome_path(self, temp_db, temp_templates_dir):
        """Test deployment without Chrome path set."""
        wps_service = WpsService(temp_db)
        wps_service.set_paths(temp_templates_dir, None, None)
        wps_service.add_script(
            name="WordScript",
            vba_code="Sub WordTest()\nEnd Sub",
            target_app="word",
            ribbon_group="WordGroup",
            ribbon_label="Word Button"
        )

        js_service = JsService(temp_db)
        # Don't set Chrome path

        service = DeploymentService(wps_service, js_service)
        result = service.deploy_all()

        # No chrome path means deploy_bookmarks returns False (not an error)
        # But Word template will fail without pywin32
        assert result['wps_word'] is False  # No COM available
        assert result['chrome_bookmarks'] is False
        # Success depends on whether WPS deployment succeeded

    @patch('core.deployment_service.DeploymentService._deploy_word_template_com')
    @patch('core.deployment_service.DeploymentService._deploy_excel_template_com')
    def test_deploy_all_creates_template_files(self, mock_excel_com, mock_word_com, deployment_service, temp_db, temp_templates_dir):
        """Test that deployment creates template files."""
        def mock_word_com_impl(scripts, template_path):
            create_mock_template(template_path, 'word')
            return {"success": True, "deployed": True, "message": "Word template created"}

        def mock_excel_com_impl(scripts, template_path):
            create_mock_template(template_path, 'excel')
            return {"success": True, "deployed": True, "message": "Excel template created"}

        mock_word_com.side_effect = mock_word_com_impl
        mock_excel_com.side_effect = mock_excel_com_impl

        deployment_service.wps_service.add_script(
            name="WordScript",
            vba_code="Sub WordTest()\nEnd Sub",
            target_app="word",
            ribbon_group="WordGroup",
            ribbon_label="Word Button"
        )
        deployment_service.wps_service.add_script(
            name="ExcelScript",
            vba_code="Sub ExcelTest()\nEnd Sub",
            target_app="excel",
            ribbon_group="ExcelGroup",
            ribbon_label="Excel Button"
        )

        result = deployment_service.deploy_all()

        # Check that template files were created in templates directory
        template_files = [f for f in os.listdir(temp_templates_dir) if f.endswith(('.dotm', '.xlam'))]
        assert len(template_files) >= 2  # At least one Word and one Excel template

    @patch('core.deployment_service.DeploymentService._deploy_word_template_com')
    def test_deploy_all_creates_bookmarks_file(self, mock_word_com, deployment_service, temp_bookmarks_dir):
        """Test that deployment creates bookmarks HTML file."""
        # Mock COM method
        def mock_word_com_impl(scripts, template_path):
            create_mock_template(template_path, 'word')
            return {"success": True, "deployed": True, "message": "Word template created"}

        mock_word_com.side_effect = mock_word_com_impl

        deployment_service.js_service.add_script(
            name="TestScript",
            url="https://example.com/test"
        )

        result = deployment_service.deploy_all()

        # Check that bookmarks file was created
        bookmarks_path = os.path.join(temp_bookmarks_dir, "Bookmarks")
        assert os.path.exists(bookmarks_path)


class TestDeployWordTemplate:
    """Test _deploy_word_template method."""

    def test_deploy_word_template_no_scripts(self, deployment_service):
        """Test Word deployment with no scripts."""
        result = deployment_service._deploy_word_template()

        assert result['success'] is True
        assert result['deployed'] is False
        assert '没有 Word 脚本需要部署' in result['message']

    def test_deploy_word_template_no_pywin32(self, deployment_service, temp_templates_dir):
        """Test Word deployment without pywin32."""
        deployment_service.wps_service.add_script(
            name="WordScript",
            vba_code="Sub WordTest()\nEnd Sub",
            target_app="word",
            ribbon_group="WordGroup",
            ribbon_label="Word Button"
        )

        with patch.object(deployment_service, '_try_com_import', return_value=False):
            result = deployment_service._deploy_word_template()

        assert result['success'] is False
        assert 'pywin32' in result['message']


class TestDeployExcelTemplate:
    """Test _deploy_excel_template method."""

    def test_deploy_excel_template_no_scripts(self, deployment_service):
        """Test Excel deployment with no scripts."""
        result = deployment_service._deploy_excel_template()

        assert result['success'] is True
        assert result['deployed'] is False
        assert '没有 Excel 脚本需要部署' in result['message']

    def test_deploy_excel_template_no_pywin32(self, deployment_service, temp_templates_dir):
        """Test Excel deployment without pywin32."""
        deployment_service.wps_service.add_script(
            name="ExcelScript",
            vba_code="Sub ExcelTest()\nEnd Sub",
            target_app="excel",
            ribbon_group="ExcelGroup",
            ribbon_label="Excel Button"
        )

        with patch.object(deployment_service, '_try_com_import', return_value=False):
            result = deployment_service._deploy_excel_template()

        assert result['success'] is False
        assert 'pywin32' in result['message']


class TestHelperMethods:
    """Test helper methods."""

    def test_build_vba_code(self, deployment_service):
        """Test VBA code generation."""
        scripts = [
            {
                'name': 'TestScript',
                'ribbon_label': 'Test Button',
                'vba_code': 'Sub TestScript()\n    MsgBox "Hello"\nEnd Sub'
            }
        ]

        vba_code = deployment_service._build_vba_code(scripts)

        assert 'Sub ScriptManager_Main()' in vba_code
        assert 'Call TestScript_Main' in vba_code
        assert 'Sub TestScript_Main()' in vba_code
        assert 'MsgBox "Hello"' in vba_code

    def test_build_ribbon_callbacks(self, deployment_service):
        """Test ribbon callback generation."""
        scripts = [
            {
                'name': 'TestScript',
                'ribbon_label': 'Test Button'
            }
        ]

        callbacks = deployment_service._build_ribbon_callbacks(scripts)

        assert 'Sub OnAction_TestScript' in callbacks
        assert 'Call TestScript_Main' in callbacks

    def test_build_custom_ui_xml(self, deployment_service):
        """Test customUI XML generation."""
        scripts = [
            {
                'name': 'TestScript',
                'ribbon_label': 'Test Button',
                'ribbon_group': 'Test Group'
            }
        ]

        xml = deployment_service._build_custom_ui_xml(scripts, 'word')

        assert '脚本管理器' in xml
        assert 'Test Group' in xml
        assert 'Test Button' in xml
        assert 'OnAction_TestScript' in xml
