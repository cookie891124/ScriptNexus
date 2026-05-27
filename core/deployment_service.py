"""Deployment service for one-click deployment of WPS templates.

Key discovery: WPS supports JavaScript macros stored in JDEData.bin (XML format).
- Ribbon config: %APPDATA%\Kingsoft\office6\customui\wps.officeUI (global for all docs)
- JS Macro templates: WPS startup directory (.dotm/.xlam with JDEData.bin)

This approach completely bypasses VBA and COM!
"""

import os
import re
import zipfile
import shutil
import glob
from datetime import datetime
from typing import Dict, Any, List, Optional
from xml.sax.saxutils import escape as xml_escape


# WPS user data directory
WPS_USERDATA_DIR = os.path.join(os.environ.get('APPDATA', ''), 'Kingsoft', 'office6')


def detect_wps_startup_dir(app: str) -> Optional[str]:
    """Auto-detect WPS startup directory for Word or Excel.

    Searches for the most recent WPS version's startup directory.

    Args:
        app: 'word' or 'excel'

    Returns:
        Path to startup directory, or None if not found.
    """
    app_dir = 'wps' if app == 'word' else 'et'
    base_paths = [
        os.path.join(os.environ.get('APPDATA', ''), 'Kingsoft', 'WPS Office'),
        os.path.join(os.environ.get('APPDATA', ''), 'Kingsoft'),
    ]

    # Find all potential startup directories
    startup_dirs = []
    for base in base_paths:
        if os.path.exists(base):
            # Search for office6/startup/{app_dir}
            pattern = os.path.join(base, '*', 'office6', 'startup', app_dir)
            for dir_path in glob.glob(pattern):
                if os.path.exists(dir_path):
                    startup_dirs.append(dir_path)

    # Return the most recent one (by version number in path)
    if startup_dirs:
        startup_dirs.sort(reverse=True)  # Higher version numbers first
        return startup_dirs[0]

    return None


class DeploymentService:
    """Service for deploying WPS ribbon UI and JS macros."""

    def __init__(self, wps_service: Any, js_service: Any,
                 word_template_dir: Optional[str] = None,
                 excel_template_dir: Optional[str] = None):
        self.wps_service = wps_service
        self.js_service = js_service
        self.word_template_dir = word_template_dir  # User-configured Word template output directory
        self.excel_template_dir = excel_template_dir  # User-configured Excel template output directory

    def _ensure_dir(self, path: str) -> bool:
        """Ensure directory exists."""
        try:
            if not os.path.exists(path):
                os.makedirs(path)
            return True
        except Exception:
            return False

    def deploy_all(self) -> Dict[str, Any]:
        """Deploy WPS Word and Excel JS macros."""
        result = {
            'success': True,
            'wps_word': False,
            'wps_excel': False,
            'errors': [],
            'messages': {}
        }

        # Deploy Word
        try:
            word_result = self._deploy_word()
            result['wps_word'] = word_result.get('deployed', False)
            result['messages']['wps_word'] = word_result.get('message', '')
            if not word_result.get('success', False) and word_result.get('message'):
                result['errors'].append(f'Word: {word_result.get("message")}')
                result['success'] = False
        except Exception as e:
            result['wps_word'] = False
            result['errors'].append(f'Word deployment error: {str(e)}')
            result['success'] = False

        # Deploy Excel
        try:
            excel_result = self._deploy_excel()
            result['wps_excel'] = excel_result.get('deployed', False)
            result['messages']['wps_excel'] = excel_result.get('message', '')
            if not excel_result.get('success', False) and excel_result.get('message'):
                result['errors'].append(f'Excel: {excel_result.get("message")}')
                result['success'] = False
        except Exception as e:
            result['wps_excel'] = False
            result['errors'].append(f'Excel deployment error: {str(e)}')
            result['success'] = False

        if result['errors'] and not (result['wps_word'] or result['wps_excel']):
            result['success'] = False

        return result

    def _deploy_word(self) -> Dict[str, Any]:
        """Deploy WPS Word ribbon UI and JS macros.

        Uses ribbon structure tables for UI, and scripts that are bound to buttons.
        """
        result = {"success": True, "deployed": False, "message": ""}

        # Get bound scripts (only those bound to buttons)
        bound_scripts = self.wps_service.get_bound_scripts("word")

        # Get ribbon structure (for UI, even if no scripts bound)
        ribbon_structure = self.wps_service.get_full_ribbon_structure("word")

        if not ribbon_structure and not bound_scripts:
            result["message"] = "没有 Word 功能区结构或绑定脚本需要部署"
            return result

        # Deploy ribbon (wps.officeUI) - uses structure tables
        ribbon_result = self._deploy_word_ribbon()
        if not ribbon_result["success"]:
            result["success"] = False
            result["message"] = ribbon_result.get("message", "Ribbon deployment failed")
            return result

        # Deploy JS macro template (only if there are bound scripts)
        if bound_scripts:
            template_result = self._deploy_word_js_macro(bound_scripts)
            if not template_result["success"]:
                result["success"] = False
                result["message"] = f"Ribbon已部署，但模板失败: {template_result.get('message', '')}"
                return result
            result["deployed"] = True
            result["message"] = (
                f"Word 部署完成！\n"
                f"- 功能区：已部署到 {ribbon_result.get('path', 'wps.officeUI')}\n"
                f"- 模板：{template_result.get('message', '')}\n"
                f"请重启 WPS Word 使功能区生效。"
            )
        else:
            result["deployed"] = True
            result["message"] = (
                f"Word 功能区已部署到 {ribbon_result.get('path', 'wps.officeUI')}\n"
                f"注意：没有绑定脚本的按钮，点击将无效果。\n"
                f"请重启 WPS Word 使功能区生效。"
            )
        return result

    def _deploy_excel(self) -> Dict[str, Any]:
        """Deploy WPS Excel ribbon UI and JS macros.

        Uses ribbon structure tables for UI, and scripts that are bound to buttons.
        """
        result = {"success": True, "deployed": False, "message": ""}

        # Get bound scripts (only those bound to buttons)
        bound_scripts = self.wps_service.get_bound_scripts("excel")

        # Get ribbon structure (for UI, even if no scripts bound)
        ribbon_structure = self.wps_service.get_full_ribbon_structure("excel")

        if not ribbon_structure and not bound_scripts:
            result["message"] = "没有 Excel 功能区结构或绑定脚本需要部署"
            return result

        # Deploy ribbon (et.officeUI) - uses structure tables
        ribbon_result = self._deploy_excel_ribbon()
        if not ribbon_result["success"]:
            result["success"] = False
            result["message"] = ribbon_result.get("message", "Ribbon deployment failed")
            return result

        # Deploy JS macro template (only if there are bound scripts)
        if bound_scripts:
            template_result = self._deploy_excel_js_macro(bound_scripts)
            if not template_result["success"]:
                result["success"] = False
                result["message"] = f"Ribbon已部署，但模板失败: {template_result.get('message', '')}"
                return result
            result["deployed"] = True
            result["message"] = (
                f"Excel 部署完成！\n"
                f"- 功能区：已部署到 {ribbon_result.get('path', 'et.officeUI')}\n"
                f"- 模板：{template_result.get('message', '')}\n"
                f"请重启 WPS Excel 使功能区生效。"
            )
        else:
            result["deployed"] = True
            result["message"] = (
                f"Excel 功能区已部署到 {ribbon_result.get('path', 'et.officeUI')}\n"
                f"注意：没有绑定脚本的按钮，点击将无效果。\n"
                f"请重启 WPS Excel 使功能区生效。"
            )
        return result

    def _build_officeui_xml(self, target_app: str) -> str:
        """Build wps.officeUI XML from ribbon structure tables.

        Uses ribbon_tabs, ribbon_groups, ribbon_buttons tables.
        Buttons without bound scripts are rendered without action.
        """
        import re

        # Get full ribbon structure
        structure = self.wps_service.get_full_ribbon_structure(target_app)

        if not structure:
            # Return empty valid XML
            return '<mso:customUI xmlns:mso="http://schemas.microsoft.com/office/2009/07/customui"><mso:ribbon><mso:tabs/></mso:ribbon></mso:customUI>'

        xml = '<mso:customUI xmlns:mso="http://schemas.microsoft.com/office/2009/07/customui">\n'
        xml += '  <mso:ribbon>\n'
        xml += '    <mso:tabs>\n'

        for tab in structure:
            tab_id = f"tab_{tab['id']}"
            xml += f'      <mso:tab label="{xml_escape(tab["name"])}" id="{xml_escape(tab_id)}">\n'

            for group in tab.get('groups', []):
                group_id = f"group_{group['id']}"
                xml += f'        <mso:group label="{xml_escape(group["name"])}" id="{xml_escape(group_id)}">\n'

                for button in group.get('buttons', []):
                    button_id = f"btn_{button['id']}"
                    btn_label = xml_escape(button['label'])

                    # Check if button has bound script
                    if button.get('script_id'):
                        # Get the actual JS code to extract real function name
                        script = self.wps_service.get_script(button['script_id'])
                        if script and script.get('js_code'):
                            # Extract actual function name from JS code
                            func_names = re.findall(r'function\s+(\w+)\s*\(', script['js_code'])
                            if func_names:
                                # Use the first function name found
                                actual_func_name = xml_escape(func_names[0])
                                xml += f'          <mso:button id="{xml_escape(button_id)}" '
                                xml += f'idM="Project.NewMacros.{actual_func_name}" '
                                xml += f'label="{btn_label}" '
                                xml += f'onAction="{actual_func_name}" '
                                xml += f'imageMso="ListMacros" />\n'
                            else:
                                # No function found - display only
                                xml += f'          <mso:button id="{xml_escape(button_id)}" '
                                xml += f'label="{btn_label}" '
                                xml += f'imageMso="ListMacros" />\n'
                        else:
                            # No script code - display only
                            xml += f'          <mso:button id="{xml_escape(button_id)}" '
                            xml += f'label="{btn_label}" '
                            xml += f'imageMso="ListMacros" />\n'
                    else:
                        # Button without action (display only)
                        xml += f'          <mso:button id="{xml_escape(button_id)}" '
                        xml += f'label="{btn_label}" '
                        xml += f'imageMso="ListMacros" />\n'

                xml += '        </mso:group>\n'

            xml += '      </mso:tab>\n'

        xml += '    </mso:tabs>\n'
        xml += '  </mso:ribbon>\n'
        xml += '</mso:customUI>'

        return xml

    def _deploy_word_ribbon(self) -> Dict[str, Any]:
        """Deploy wps.officeUI file using ribbon structure tables."""
        result = {"success": False, "message": "", "path": ""}

        customui_dir = os.path.join(WPS_USERDATA_DIR, 'customui')
        if not self._ensure_dir(customui_dir):
            result["message"] = f"无法创建目录：{customui_dir}"
            return result

        officeui_xml = self._build_officeui_xml('word')
        officeui_path = os.path.join(customui_dir, 'wps.officeUI')

        try:
            with open(officeui_path, 'w', encoding='utf-8') as f:
                f.write(officeui_xml)
            result["success"] = True
            result["path"] = officeui_path
        except Exception as e:
            result["message"] = f"无法写入 {officeui_path}: {e}"

        return result

    def _deploy_excel_ribbon(self) -> Dict[str, Any]:
        """Deploy et.officeUI file using ribbon structure tables."""
        result = {"success": False, "message": "", "path": ""}

        customui_dir = os.path.join(WPS_USERDATA_DIR, 'customui')
        if not self._ensure_dir(customui_dir):
            result["message"] = f"无法创建目录：{customui_dir}"
            return result

        officeui_xml = self._build_officeui_xml('excel')
        officeui_path = os.path.join(customui_dir, 'et.officeUI')

        try:
            with open(officeui_path, 'w', encoding='utf-8') as f:
                f.write(officeui_xml)
            result["success"] = True
            result["path"] = officeui_path
        except Exception as e:
            result["message"] = f"无法写入 {officeui_path}: {e}"

        return result

    def _generate_js_code(self, scripts: List[Dict]) -> str:
        """Generate JavaScript code from scripts."""
        js_code = ""
        for script in scripts:
            func_name = script['name']
            code = script.get('js_code', script.get('vba_code', ''))

            # If code already contains function definitions, use it as-is
            if 'function ' in code:
                # Convert tabs to spaces to preserve indentation in WPS XML
                js_code += code.strip().replace('\t', '    ') + '\n\n'
            else:
                # Wrap plain code (no function wrapper) in a JS function
                js_code += f"function {func_name}() {{\n"
                lines = code.strip().split('\n')
                body_lines = []
                skip_first = lines and ('Sub ' in lines[0] or 'Function ' in lines[0])
                skip_last = lines and lines[-1].strip() in ('End Sub', 'End Function')

                for j, line in enumerate(lines):
                    if j == 0 and skip_first:
                        continue
                    if j == len(lines) - 1 and skip_last:
                        continue
                    body_lines.append(line)

                # Add body lines preserving relative indentation
                for line in body_lines:
                    stripped = line.strip()
                    if stripped:
                        js_code += f"    {stripped}\n"

                js_code += "}\n\n"

        return js_code

    def _generate_jdedata_bin(self, js_code: str) -> str:
        """Generate JDEData.bin XML with JS code.

        Format matches WPS recorded macro structure exactly.
        """
        escaped_code = js_code.replace('\t', '    ')  # tabs to spaces before XML (WPS drops tabs)
        escaped_code = escaped_code.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        escaped_code = escaped_code.replace('\n', '&#x0A;').replace('\r', '&#x0D;')

        # Extract function names from JS code for functionsdata
        import re
        func_names = re.findall(r'function\s+(\w+)\s*\(', js_code)

        # Build functionsdata in WPS recorded macro format
        functionsdata = ''
        for name in func_names:
            functionsdata += f'''<functiondata name="{name}">
            <shortcut></shortcut>
            <description></description>
        </functiondata>'''

        return f'''<?xml version="1.0" encoding="UTF-8" ?>
<document version="2.0">
    <name>Project</name>
    <property desc="" lock="false" password="" />
    <activemodule>1</activemodule>
    <codemodule name="NewMacros" id="1">
        <window cursorpos="84" actived="true" visible="true" />
        <codetext>{escaped_code}</codetext>
    </codemodule>
    <functionsdata>{functionsdata}</functionsdata>
</document>'''

    def _deploy_word_js_macro(self, scripts: List[Dict]) -> Dict[str, Any]:
        """Deploy Word JS macro template (.dotm).

        Only writes to user-configured word_template_dir.
        """
        result = {"success": False, "message": ""}

        target_dir = self.word_template_dir
        if not target_dir or not target_dir.strip():
            result["message"] = "请在设置中配置「Word 模板目录」"
            return result

        if not os.path.exists(target_dir):
            if not self._ensure_dir(target_dir):
                result["message"] = f"无法创建目录：{target_dir}"
                return result

        template_name = "WpsScriptManager_Word.dotm"
        template_path = os.path.join(target_dir, template_name)

        try:
            self._generate_js_macro_dotm(scripts, template_path, 'word')
            result["success"] = True
            result["message"] = f"{template_name} -> {target_dir}"
        except Exception as e:
            result["message"] = str(e)

        return result

    def _deploy_excel_js_macro(self, scripts: List[Dict]) -> Dict[str, Any]:
        """Deploy Excel JS macro template (.xlam).

        Uses recorded xlam template as base for reliable structure.
        """
        result = {"success": False, "message": ""}

        target_dir = self.excel_template_dir
        if not target_dir or not target_dir.strip():
            result["message"] = "请在设置中配置「Excel 模板目录」"
            return result

        if not os.path.exists(target_dir):
            if not self._ensure_dir(target_dir):
                result["message"] = f"无法创建目录：{target_dir}"
                return result

        template_name = "WpsScriptManager_Excel.xlam"
        template_path = os.path.join(target_dir, template_name)

        try:
            self._generate_js_macro_xltm(scripts, template_path)
            result["success"] = True
            result["message"] = f"{template_name} -> {target_dir}"
        except Exception as e:
            result["message"] = str(e)

        return result

    def _generate_js_macro_dotm(self, scripts: List[Dict], output_path: str, app_type: str = 'word'):
        """Generate a .dotm file with JS macros.

        Structure matches WPS recorded macro template exactly.
        """
        js_code = self._generate_js_code(scripts)
        jde_content = self._generate_jdedata_bin(js_code)

        # Content_Types matching recorded macro structure
        content_types = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/custom.xml" ContentType="application/vnd.openxmlformats-officedocument.custom-properties+xml"/>
  <Override PartName="/word/JDEData.bin" ContentType="application/octet-stream"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.ms-word.document.macroEnabled.main+xml"/>
  <Override PartName="/word/fontTable.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.fontTable+xml"/>
  <Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
  <Override PartName="/word/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
</Types>'''

        # Root relationships
        rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/custom-properties" Target="docProps/custom.xml"/>
  <Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>'''

        # Document relationships matching recorded macro (JDEData at rId5)
        doc_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings" Target="settings.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="theme/theme1.xml"/>
  <Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/fontTable" Target="fontTable.xml"/>
  <Relationship Id="rId5" Type="http://www.wps.cn/officeDocument/2018/jdeExtension" Target="JDEData.bin"/>
</Relationships>'''

        document = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas" xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:w10="urn:schemas-microsoft-com:office:word" xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup" xmlns:wpi="http://schemas.microsoft.com/office/word/2010/wordprocessingInk" xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml/equation" xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape" mc:Ignorable="w14 wp14">
  <w:body>
    <w:p>
      <w:r>
        <w:t>WPS Script Manager Template</w:t>
      </w:r>
    </w:p>
    <w:sectPr>
      <w:pgSz w:w="12240" w:h="15840"/>
      <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/>
    </w:sectPr>
  </w:body>
</w:document>'''

        # Minimal styles matching recorded macro
        styles = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:docDefaults>
    <w:rPrDefault>
      <w:rPr>
        <w:rFonts w:asciiTheme="minorHAnsi" w:eastAsiaTheme="minorEastAsia" w:hAnsiTheme="minorHAnsi" w:cstheme="minorBidi"/>
        <w:kern w:val="2"/>
        <w:sz w:val="24"/>
        <w:szCs w:val="24"/>
      </w:rPr>
    </w:rPrDefault>
  </w:docDefaults>
</w:styles>'''

        # Minimal settings
        settings = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:settings xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:zoom w:percent="100"/>
</w:settings>'''

        # Minimal font table
        fontTable = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:fonts xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:font w:name="Times New Roman">
    <w:panose1 w:val="02020603050405020304"/>
    <w:charset w:val="00"/>
  </w:font>
</w:fonts>'''

        # Minimal theme
        theme = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Office Theme">
  <a:themeElements>
    <a:clrScheme name="Office">
      <a:dk1><a:sysClr val="windowText" lastClr="000000"/></a:dk1>
      <a:lt1><a:sysClr val="window" lastClr="FFFFFF"/></a:lt1>
    </a:clrScheme>
    <a:fontScheme name="Office">
      <a:majorFont><a:latin typeface="Calibri"/></a:majorFont>
      <a:minorFont><a:latin typeface="Calibri"/></a:minorFont>
    </a:fontScheme>
  </a:themeElements>
</a:theme>'''

        # Minimal docProps
        app_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">
  <Application>WPS Office</Application>
  <AppVersion>12.0000</AppVersion>
</Properties>'''

        core_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:creator>WPS Script Manager</dc:creator>
  <dcterms:created xsi:type="dcterms:W3CDTF">2024-01-01T00:00:00Z</dcterms:created>
</cp:coreProperties>'''

        custom_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/custom-properties">
</Properties>'''

        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr('[Content_Types].xml', content_types)
            zf.writestr('_rels/.rels', rels)
            zf.writestr('docProps/app.xml', app_xml)
            zf.writestr('docProps/core.xml', core_xml)
            zf.writestr('docProps/custom.xml', custom_xml)
            zf.writestr('word/_rels/document.xml.rels', doc_rels)
            zf.writestr('word/document.xml', document)
            zf.writestr('word/styles.xml', styles)
            zf.writestr('word/settings.xml', settings)
            zf.writestr('word/fontTable.xml', fontTable)
            zf.writestr('word/theme/theme1.xml', theme)
            zf.writestr('word/JDEData.bin', jde_content.encode('utf-8'))

    def _generate_js_macro_xltm(self, scripts: List[Dict], output_path: str):
        """Generate a .xlam file with JS macros for Excel.

        Uses recorded macro template as base for reliable structure.
        """
        import shutil
        import tempfile

        js_code = self._generate_js_code(scripts)
        jde_content = self._generate_jdedata_bin(js_code)

        # Use recorded xlam template as base (addin.macroEnabled format)
        base_template = os.path.join(os.path.dirname(__file__), '..', 'tests', '工作簿1.xlam')
        if not os.path.exists(base_template):
            # Fallback to manual creation if base template not found
            self._generate_js_macro_xltm_manual(scripts, output_path)
            return

        # Create temp directory
        temp_dir = tempfile.mkdtemp()

        try:
            # Extract base template
            with zipfile.ZipFile(base_template, 'r') as z:
                z.extractall(temp_dir)

            # Replace JDEData.bin
            jde_path = os.path.join(temp_dir, 'xl', 'JDEData.bin')
            with open(jde_path, 'w', encoding='utf-8') as f:
                f.write(jde_content)

            # Repack as new xlam
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as z:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arc_name = os.path.relpath(file_path, temp_dir)
                        z.write(file_path, arc_name)
        finally:
            # Clean up temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _generate_js_macro_xltm_manual(self, scripts: List[Dict], output_path: str):
        """Generate a .xltm file manually (fallback when base template not found)."""
        js_code = self._generate_js_code(scripts)
        jde_content = self._generate_jdedata_bin(js_code)

        # Content_Types matching recorded macro structure
        # Critical: workbook.xml uses addin.macroEnabled ContentType for .xlam
        content_types = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/><Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/><Override PartName="/docProps/custom.xml" ContentType="application/vnd.openxmlformats-officedocument.custom-properties+xml"/><Override PartName="/xl/JDEData.bin" ContentType="application/octet-stream"/><Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/><Override PartName="/xl/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.ms-excel.addin.macroEnabled.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>'''

        # Root relationships - workbook is rId1
        rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/custom-properties" Target="docProps/custom.xml"/>
</Relationships>'''

        # Workbook relationships matching recorded macro
        # CRITICAL: JDEData uses rId3, worksheet uses rId1, styles uses rId4
        workbook_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="theme/theme1.xml"/>
  <Relationship Id="rId3" Type="http://www.wps.cn/officeDocument/2018/jdeExtension" Target="JDEData.bin"/>
  <Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>'''

        workbook = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <fileVersion appName="xl" lastEdited="3" lowestEdited="5" rupBuild="9302"/>
  <workbookPr codeName="ThisWorkbook"/>
  <bookViews>
    <workbookView windowWidth="28800" windowHeight="12255"/>
  </bookViews>
  <sheets>
    <sheet name="Sheet1" sheetId="1" r:id="rId1"/>
  </sheets>
  <calcPr calcId="191029"/>
</workbook>'''

        sheet1 = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetData/>
</worksheet>'''

        # Minimal styles
        styles = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="1">
    <font><sz val="11"/><name val="Calibri"/></font>
  </fonts>
  <fills count="2">
    <fill><patternFill patternType="none"/></fill>
    <fill><patternFill patternType="gray125"/></fill>
  </fills>
  <borders count="1">
    <border><left/><right/><top/><bottom/><diagonal/></border>
  </borders>
  <cellStyleXfs count="1">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0"/>
  </cellStyleXfs>
  <cellXfs count="1">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
  </cellXfs>
</styleSheet>'''

        # Minimal theme
        theme = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Office Theme">
  <a:themeElements>
    <a:clrScheme name="Office">
      <a:dk1><a:sysClr val="windowText" lastClr="000000"/></a:dk1>
      <a:lt1><a:sysClr val="window" lastClr="FFFFFF"/></a:lt1>
    </a:clrScheme>
    <a:fontScheme name="Office">
      <a:majorFont><a:latin typeface="Calibri"/></a:majorFont>
      <a:minorFont><a:latin typeface="Calibri"/></a:minorFont>
    </a:fontScheme>
  </a:themeElements>
</a:theme>'''

        # Minimal docProps
        app_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">
  <Application>WPS Office</Application>
  <AppVersion>12.0000</AppVersion>
</Properties>'''

        core_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:creator>WPS Script Manager</dc:creator>
  <dcterms:created xsi:type="dcterms:W3CDTF">2024-01-01T00:00:00Z</dcterms:created>
</cp:coreProperties>'''

        custom_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/custom-properties">
</Properties>'''

        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr('[Content_Types].xml', content_types)
            zf.writestr('_rels/.rels', rels)
            zf.writestr('docProps/app.xml', app_xml)
            zf.writestr('docProps/core.xml', core_xml)
            zf.writestr('docProps/custom.xml', custom_xml)
            zf.writestr('xl/_rels/workbook.xml.rels', workbook_rels)
            zf.writestr('xl/workbook.xml', workbook)
            zf.writestr('xl/worksheets/sheet1.xml', sheet1)
            zf.writestr('xl/styles.xml', styles)
            zf.writestr('xl/theme/theme1.xml', theme)
            zf.writestr('xl/JDEData.bin', jde_content.encode('utf-8'))

    def check_deployment_status(self) -> Dict[str, str]:
        """Check current deployment status for tray display.

        Returns:
            Dictionary with 'word', 'excel' keys
            Values: 'ok', 'partial', 'error', 'unknown'
        """
        result = {
            'word': 'unknown',
            'excel': 'unknown',
        }

        # Check Word ribbon deployment
        word_ribbon_path = os.path.join(WPS_USERDATA_DIR, 'customui', 'wps.officeUI')
        if os.path.exists(word_ribbon_path):
            # Check if it contains our custom ribbon
            try:
                with open(word_ribbon_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if '脚本管理' in content or 'ScriptNexus' in content:
                        result['word'] = 'ok'
                    else:
                        result['word'] = 'error'
            except Exception:
                result['word'] = 'unknown'
        else:
            result['word'] = 'error'

        # Check Excel ribbon deployment
        excel_ribbon_path = os.path.join(WPS_USERDATA_DIR, 'customui', 'et.officeUI')
        if os.path.exists(excel_ribbon_path):
            try:
                with open(excel_ribbon_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if '脚本管理' in content or 'ScriptNexus' in content:
                        result['excel'] = 'ok'
                    else:
                        result['excel'] = 'error'
            except Exception:
                result['excel'] = 'unknown'
        else:
            result['excel'] = 'error'

        return result

