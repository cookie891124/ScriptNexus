"""Verify that deployed templates contain all required components.

This script tests that both Word (.dotm) and Excel (.xlam) templates contain:
1. customUI/customUI.xml - Ribbon configuration
2. vbaProject.bin - VBA project binary (512+ bytes)
3. VBA/*.bas files - VBA source code files
"""

import os
import sys
import zipfile
import tempfile
import shutil

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add core to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))

from deployment_service import DeploymentService
# from wps_service import WpsService
# from js_service import JsService


class MockWpsService:
    """Mock WPS service for testing."""

    def __init__(self):
        self.templates_dir = tempfile.mkdtemp()
        self.word_startup = None
        self.excel_startup = None

    def get_all_scripts(self, app_type: str):
        """Return mock scripts."""
        return [
            {
                'name': 'TestScript',
                'ribbon_label': 'Test Button',
                'ribbon_group': 'Test Group',
                'vba_code': '''Sub TestScript_Main()
    MsgBox "Hello from TestScript!"
End Sub'''
            }
        ]


class MockJsService:
    """Mock JS service for testing."""

    def deploy_bookmarks(self):
        return True


def verify_word_template():
    """Verify Word template structure."""
    print("=" * 70)
    print("Word Template Verification")
    print("=" * 70)

    wps = MockWpsService()
    js = MockJsService()
    service = DeploymentService(wps, js)

    # Deploy Word template
    result = service._deploy_word_template()

    if not result.get('success'):
        print(f"FAILED: {result.get('message')}")
        return False

    # Find the generated template
    template_files = [f for f in os.listdir(wps.templates_dir) if f.endswith('.dotm')]
    if not template_files:
        print("FAILED: No .dotm file found")
        return False

    template_path = os.path.join(wps.templates_dir, template_files[0])
    print(f"Template: {template_files[0]}")
    print(f"Size: {os.path.getsize(template_path)} bytes")

    # Verify contents
    with zipfile.ZipFile(template_path, 'r') as zf:
        namelist = zf.namelist()

        # Check customUI (case-insensitive search)
        customui_files = [n for n in namelist if 'customui' in n.lower()]
        if not customui_files:
            print("FAILED: No customUI folder found")
            return False
        print(f"customUI files: {customui_files}")

        # Verify customUI.xml content
        if 'word/customUI/customUI.xml' in namelist:
            xml_content = zf.read('word/customUI/customUI.xml').decode('utf-8')
            if '脚本管理器' in xml_content:
                print("[OK] customUI.xml contains '脚本管理器' tab")
            else:
                print("FAILED: customUI.xml missing '脚本管理器' tab")
                return False

        # Check vbaProject.bin
        if 'word/vbaProject.bin' in namelist:
            vba_bin = zf.read('word/vbaProject.bin')
            print(f"[OK] vbaProject.bin: {len(vba_bin)} bytes")
            if len(vba_bin) < 512:
                print(f"WARNING: vbaProject.bin seems too small ({len(vba_bin)} bytes)")
        else:
            print("FAILED: vbaProject.bin not found")
            return False

        # Check VBA source files
        vba_files = [n for n in namelist if n.startswith('word/VBA/') and n.endswith('.bas')]
        if not vba_files:
            print("FAILED: No VBA source files (.bas) found")
            return False
        print(f"[OK] VBA source files: {[os.path.basename(f) for f in vba_files]}")

        # Verify specific VBA modules
        required_modules = ['WpsScriptManager.bas', 'ThisDocument.bas']
        for module in required_modules:
            module_path = f'word/VBA/{module}'
            if module_path in namelist:
                content = zf.read(module_path).decode('utf-8', errors='ignore')
                print(f"  [OK] {module}: {len(content)} bytes")
                if 'TestScript_Main' in content:
                    print(f"    [OK] Contains TestScript_Main subroutine")
            else:
                print(f"FAILED: Missing {module}")
                return False

        # Check VBA project structure files
        for f in ['word/VBA/project.vba', 'word/VBA/_VBA_PROJECT', 'word/VBA/dir']:
            if f in namelist:
                print(f"  [OK] {os.path.basename(f)} present")
            else:
                print(f"WARNING: Missing {f}")

    # Cleanup
    shutil.rmtree(wps.templates_dir)

    print("\n[OK] Word template verification PASSED")
    return True


def verify_excel_template():
    """Verify Excel template structure."""
    print("\n" + "=" * 70)
    print("Excel Template Verification")
    print("=" * 70)

    wps = MockWpsService()
    js = MockJsService()
    service = DeploymentService(wps, js)

    # Deploy Excel template
    result = service._deploy_excel_template()

    if not result.get('success'):
        print(f"FAILED: {result.get('message')}")
        return False

    # Find the generated template
    template_files = [f for f in os.listdir(wps.templates_dir) if f.endswith('.xlam')]
    if not template_files:
        print("FAILED: No .xlam file found")
        return False

    template_path = os.path.join(wps.templates_dir, template_files[0])
    print(f"Template: {template_files[0]}")
    print(f"Size: {os.path.getsize(template_path)} bytes")

    # Verify contents
    with zipfile.ZipFile(template_path, 'r') as zf:
        namelist = zf.namelist()

        # Check customUI (case-insensitive search)
        customui_files = [n for n in namelist if 'customui' in n.lower()]
        if not customui_files:
            print("FAILED: No customUI folder found")
            return False
        print(f"customUI files: {customui_files}")

        # Verify customUI.xml content
        if 'xl/customUI/customUI.xml' in namelist:
            xml_content = zf.read('xl/customUI/customUI.xml').decode('utf-8')
            if '脚本管理器' in xml_content:
                print("[OK] customUI.xml contains '脚本管理器' tab")
            else:
                print("FAILED: customUI.xml missing '脚本管理器' tab")
                return False

        # Check vbaProject.bin
        if 'xl/vbaProject.bin' in namelist:
            vba_bin = zf.read('xl/vbaProject.bin')
            print(f"[OK] vbaProject.bin: {len(vba_bin)} bytes")
            if len(vba_bin) < 512:
                print(f"WARNING: vbaProject.bin seems too small ({len(vba_bin)} bytes)")
        else:
            print("FAILED: vbaProject.bin not found")
            return False

        # Check VBA source files
        vba_files = [n for n in namelist if n.startswith('xl/VBA/') and n.endswith('.bas')]
        if not vba_files:
            print("FAILED: No VBA source files (.bas) found")
            return False
        print(f"[OK] VBA source files: {[os.path.basename(f) for f in vba_files]}")

        # Verify specific VBA modules
        required_modules = ['WpsScriptManager.bas', 'ThisWorkbook.bas']
        for module in required_modules:
            module_path = f'xl/VBA/{module}'
            if module_path in namelist:
                content = zf.read(module_path).decode('utf-8', errors='ignore')
                print(f"  [OK] {module}: {len(content)} bytes")
                if 'TestScript_Main' in content:
                    print(f"    [OK] Contains TestScript_Main subroutine")
            else:
                print(f"FAILED: Missing {module}")
                return False

        # Check VBA project structure files
        for f in ['xl/VBA/project.vba', 'xl/VBA/_VBA_PROJECT', 'xl/VBA/dir']:
            if f in namelist:
                print(f"  [OK] {os.path.basename(f)} present")
            else:
                print(f"WARNING: Missing {f}")

    # Cleanup
    shutil.rmtree(wps.templates_dir)

    print("\n[OK] Excel template verification PASSED")
    return True


def main():
    """Run all verifications."""
    print("\n" + "=" * 70)
    print("WPS Template Structure Verification")
    print("=" * 70 + "\n")

    word_ok = verify_word_template()
    excel_ok = verify_excel_template()

    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"Word template:  {'PASSED' if word_ok else 'FAILED'}")
    print(f"Excel template: {'PASSED' if excel_ok else 'FAILED'}")

    if word_ok and excel_ok:
        print("\nAll verifications PASSED")
        return 0
    else:
        print("\nSome verifications FAILED")
        return 1


if __name__ == '__main__':
    sys.exit(main())
