"""Extract vbaProject.bin from a macro-enabled Office file.

Usage: python extract_vba.py source.xlam [output_dir]

This creates vbaProject_excel.bin or vbaProject_word.bin in the templates directory.
"""

import os
import sys
import zipfile
import shutil


def extract_vba_project(source_file: str, output_dir: str) -> bool:
    """Extract vbaProject.bin from a macro-enabled file."""
    if not os.path.exists(source_file):
        print(f"文件不存在：{source_file}")
        return False

    ext = os.path.splitext(source_file)[1].lower()
    if ext not in ['.xlam', '.xlsm', '.dotm', '.docm']:
        print(f"不支持的文件类型：{ext}")
        return False

    # Determine internal path and output name
    if ext in ['.xlam', '.xlsm']:
        vba_path = 'xl/vbaProject.bin'
        output_name = 'vbaProject_excel.bin'
    else:
        vba_path = 'word/vbaProject.bin'
        output_name = 'vbaProject_word.bin'

    try:
        with zipfile.ZipFile(source_file, 'r') as zf:
            if vba_path not in zf.namelist():
                print(f"文件中未找到 VBA 项目：{vba_path}")
                print("请确保文件包含 VBA 宏代码。")
                return False

            vba_data = zf.read(vba_path)
            output_path = os.path.join(output_dir, output_name)

            with open(output_path, 'wb') as f:
                f.write(vba_data)

            # Also save generic vbaProject.bin
            generic_path = os.path.join(output_dir, 'vbaProject.bin')
            with open(generic_path, 'wb') as f:
                f.write(vba_data)

            print(f"✓ 提取成功：{output_path}")
            print(f"  文件大小：{len(vba_data)} bytes")
            print(f"  同时保存：{generic_path}")
            return True

    except zipfile.BadZipFile:
        print(f"错误：文件不是有效的 ZIP 格式")
        return False
    except Exception as e:
        print(f"错误：{e}")
        return False


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法：python extract_vba.py <source_file> [output_dir]")
        print("\n示例:")
        print("  python extract_vba.py template.xlam templates/")
        sys.exit(1)

    source = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else 'templates'

    if not os.path.exists(output):
        os.makedirs(output)

    success = extract_vba_project(source, output)
    sys.exit(0 if success else 1)
