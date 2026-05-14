"""在内网环境生成 VBA 种子文件的辅助脚本。

使用方法（在内网）：
1. 运行此脚本生成基础模板和 VBA 代码文件
2. 在 WPS 中打开生成的 .xlam 文件
3. 按 Alt+F11，导入 .bas 文件
4. 保存文件
5. 运行 extract_vba.py 提取 vbaProject.bin
"""

import os
import zipfile
from datetime import datetime


def create_seed_excel(output_dir: str = "templates") -> str:
    """创建一个基础的 Excel 种子文件 (.xlam)。"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"seed_template_{timestamp}.xlam"
    filepath = os.path.join(output_dir, filename)

    try:
        with zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr('[Content_Types].xml', '''<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
    <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
    <Override PartName="/xl/workbook.xml" ContentType="application/vnd.ms-excel.sheet.macroEnabled.main+xml"/>
    <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.ms-excel.worksheet.macroEnabled.sheet+xml"/>
    <Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>
    <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
</Types>''')

            zf.writestr('_rels/.rels', '''<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>''')

            zf.writestr('xl/workbook.xml', '''<?xml version="1.0" encoding="UTF-8"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
    <fileVersion appName="xl" lastEdited="7"/>
    <workbookPr date1904="false"/>
    <sheets><sheet name="Sheet1" sheetId="1" r:id="rId1"/></sheets>
</workbook>''')

            zf.writestr('xl/_rels/workbook.xml.rels', '''<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
    <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" Target="sharedStrings.xml"/>
    <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>''')

            zf.writestr('xl/worksheets/sheet1.xml', '''<?xml version="1.0" encoding="UTF-8"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
    <dimension ref="A1:A1"/>
    <sheetViews><sheetView workbookViewId="0" tabSelected="1"/></sheetViews>
    <sheetData/>
</worksheet>''')

            zf.writestr('xl/sharedStrings.xml', '''<?xml version="1.0" encoding="UTF-8"?>
<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="1" uniqueCount="1">
    <si><t>WPS Script Manager Seed Template</t></si>
</sst>''')

            zf.writestr('xl/styles.xml', '''<?xml version="1.0" encoding="UTF-8"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"/>''')

        print(f"[OK] Excel 种子模板已创建：{filepath}")
        return filepath

    except Exception as e:
        print(f"[ERROR] Excel 创建失败：{e}")
        return None


def create_seed_dotm(output_dir: str = "templates") -> str:
    """创建一个基础的 Word 种子文件 (.dotm)。"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"seed_template_{timestamp}.dotm"
    filepath = os.path.join(output_dir, filename)

    try:
        with zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr('[Content_Types].xml', '''<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
    <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
    <Override PartName="/word/document.xml" ContentType="application/vnd.ms-word.document.macroEnabled.main+xml"/>
    <Override PartName="/word/settings.xml" ContentType="application/vnd.ms-word.settings+xml"/>
    <Override PartName="/word/styles.xml" ContentType="application/vnd.ms-word.styles+xml"/>
    <Override PartName="/word/fontTable.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.fontTable+xml"/>
</Types>''')

            zf.writestr('_rels/.rels', '''<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>''')

            zf.writestr('word/document.xml', '''<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body><w:p><w:r><w:t>WPS Script Manager Seed Template</w:t></w:r></w:p>
</w:body></w:document>''')

            zf.writestr('word/_rels/document.xml.rels', '''<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings" Target="settings.xml"/>
    <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
    <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/fontTable" Target="fontTable.xml"/>
</Relationships>''')

            zf.writestr('word/settings.xml', '''<?xml version="1.0" encoding="UTF-8"?>
<w:settings xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:compat/><w:docVars><w:docVar w:name="MSPROCESSING" w:val="1"/></w:docVars>
</w:settings>''')

            zf.writestr('word/styles.xml', '''<?xml version="1.0" encoding="UTF-8"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:docDefaults><w:rPrDefault><w:rPr>
        <w:rFonts w:asciiTheme="minorHAnsi"/><w:sz w:val="24"/><w:szCs w:val="24"/>
    </w:rPr></w:rPrDefault></w:docDefaults>
</w:styles>''')

            zf.writestr('word/fontTable.xml', '''<?xml version="1.0" encoding="UTF-8"?>
<w:fonts xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:font w:name="Calibri"><w:panose1 w:val="020F0502020204030204"/></w:font>
</w:fonts>''')

        print(f"[OK] Word 种子模板已创建：{filepath}")
        return filepath

    except Exception as e:
        print(f"[ERROR] Excel 创建失败：{e}")
        return None


def create_sample_vba() -> str:
    """创建示例 VBA 代码文件。"""
    vba_code = '''
' WPS Script Manager 示例 VBA 宏
' 将此代码导入种子文件后保存，然后使用 extract_vba.py 提取 vbaProject.bin

Sub ScriptManager_Main()
    ' 主入口函数
    Call HelloWPS_Main
End Sub

Sub HelloWPS_Main()
    ' 示例宏：Hello WPS
    MsgBox "Hello from WPS Script Manager!", vbInformation, "WPS 脚本管理器"
End Sub

Sub InsertCurrentDate_Main()
    ' 示例宏：插入当前日期
    ActiveCell.Value = Date
End Sub
'''

    # 保存为 .bas 文件
    output_path = os.path.join("templates", "sample_vba.bas")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(vba_code)

    print(f"[OK] 示例 VBA 代码已创建：{output_path}")
    return output_path


def main():
    """主函数：在内网环境运行，生成种子模板和示例 VBA 代码。"""
    print("=" * 50)
    print("内网 VBA 种子文件生成工具")
    print("=" * 50)
    print()

    output_dir = "templates"

    # 创建种子文件
    excel_path = create_seed_excel(output_dir)
    word_path = create_seed_dotm(output_dir)

    # 创建示例 VBA 代码
    vba_path = create_sample_vba()

    print()
    print("=" * 50)
    print("操作步骤:")
    print("=" * 50)
    print()
    print("1. 在 WPS 中打开种子文件:")
    print(f"   Excel: {excel_path}")
    print(f"   Word:  {word_path}")
    print()
    print("2. 按 Alt+F11 打开 VBA 编辑器")
    print()
    print("3. 文件 → 导入文件，选择：")
    print(f"   {vba_path}")
    print()
    print("4. 保存文件（另存为 .xlam 或 .dotm）")
    print()
    print("5. 运行提取工具:")
    print(f"   python tools/extract_vba.py your_seed.xlam {output_dir}/")
    print()
    print("6. 生成的 vbaProject.bin 可用于一键部署")
    print()


if __name__ == '__main__':
    main()
