"""验证模板结构是否与录制宏文件匹配"""

import os
import zipfile
import sys

# 添加项目根目录到路径
sys.path.insert(0, 'D:/ScriptNexus')

from core.deployment_service import DeploymentService


def extract_and_compare(template_path: str, reference_path: str, app_type: str):
    """比较生成的模板与参考模板的结构"""

    print(f"\n=== 比较模板结构 ===")
    print(f"生成的模板: {template_path}")
    print(f"参考模板: {reference_path}")

    # 提取文件列表
    with zipfile.ZipFile(template_path, 'r') as z:
        generated_files = sorted(z.namelist())

    with zipfile.ZipFile(reference_path, 'r') as z:
        reference_files = sorted(z.namelist())

    print(f"\n生成的文件列表 ({len(generated_files)} 个):")
    for f in generated_files:
        print(f"  {f}")

    print(f"\n参考文件列表 ({len(reference_files)} 个):")
    for f in reference_files:
        print(f"  {f}")

    # 检查关键差异
    print(f"\n=== 关键结构检查 ===")

    # 检查 JDEData.bin 位置
    jde_location = 'word/JDEData.bin' if app_type == 'word' else 'xl/JDEData.bin'
    if jde_location in generated_files:
        print(f"[OK] JDEData.bin located at: {jde_location}")
    else:
        print(f"[ERROR] JDEData.bin location incorrect")

    # 检查 Content_Types.xml 中的 macroEnabled ContentType
    with zipfile.ZipFile(template_path, 'r') as z:
        content_types = z.read('[Content_Types].xml').decode('utf-8')

    expected_ct = 'application/vnd.ms-word.document.macroEnabled.main+xml' if app_type == 'word' else 'application/vnd.ms-excel.template.macroEnabled.main+xml'

    if expected_ct in content_types:
        print(f"[OK] Content_Types.xml contains correct macroEnabled ContentType")
    else:
        print(f"[ERROR] Content_Types.xml ContentType may be incorrect")
        print(f"   Expected: {expected_ct}")
        print(f"   Content snippet: {content_types[:500]}")

    # 检查 workbook.xml.rels 中的 JDEData 关系 ID
    if app_type == 'excel':
        rels_path = 'xl/_rels/workbook.xml.rels'
        with zipfile.ZipFile(template_path, 'r') as z:
            rels_content = z.read(rels_path).decode('utf-8')

        if 'rId3' in rels_content and 'jdeExtension' in rels_content:
            print(f"[OK] Excel JDEData uses rId3 (correct)")
        else:
            print(f"[ERROR] Excel JDEData relationship ID may be wrong")
            print(f"   Content: {rels_content}")

        with zipfile.ZipFile(reference_path, 'r') as z:
            ref_rels = z.read(rels_path).decode('utf-8')
        print(f"\nReference workbook.xml.rels:\n{ref_rels}")

    # 检查 JDEData.bin 内容
    with zipfile.ZipFile(template_path, 'r') as z:
        jde_content = z.read(jde_location).decode('utf-8')

    print(f"\n=== JDEData.bin Content ===")
    print(jde_content[:1000])

    if '<functiondata' in jde_content:
        print(f"[OK] JDEData.bin uses correct functiondata format")
    else:
        print(f"[ERROR] JDEData.bin format may be incorrect")


def main():
    """生成测试模板并与录制宏文件比较"""

    # 创建测试脚本
    test_scripts = [
        {
            'name': 'TestMacro',
            'js_code': '''function TestMacro() {
    Selection.TypeText("Hello World");
}'''
        }
    ]

    # 创建临时 DeploymentService
    class MockWpsService:
        templates_dir = None
        word_startup = None
        excel_startup = None

    class MockJsService:
        pass

    deployment_service = DeploymentService(MockWpsService(), MockJsService())

    # 生成 Word 模板
    word_template_path = 'D:/ScriptNexus/tests/test_generated_word.dotm'
    reference_word_path = 'D:/ScriptNexus/tests/123.docm'

    print("生成 Word 测试模板...")
    deployment_service._generate_js_macro_dotm(test_scripts, word_template_path, 'word')

    if os.path.exists(word_template_path) and os.path.exists(reference_word_path):
        extract_and_compare(word_template_path, reference_word_path, 'word')

    # 生成 Excel 模板
    excel_template_path = 'D:/ScriptNexus/tests/test_generated_excel.xlam'
    reference_excel_path = 'D:/ScriptNexus/tests/工作簿1.xltm'

    print("\n\n生成 Excel 测试模板...")
    deployment_service._generate_js_macro_xlam(test_scripts, excel_template_path)

    if os.path.exists(excel_template_path) and os.path.exists(reference_excel_path):
        extract_and_compare(excel_template_path, reference_excel_path, 'excel')

    print("\n=== 测试完成 ===")


if __name__ == '__main__':
    main()