"""
从内网环境的模板文件中提取功能区 (Ribbon) 配置

运行方式:
python extract_ribbon_config.py [template_file]

如果没有指定 template_file，则自动扫描常用目录

输出:
- customUI XML 内容
- VBA 回调函数定义
"""

import sys
import os
import zipfile

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def extract_custom_ui(template_path: str) -> None:
    """Extract customUI XML from template."""
    print(f"=== 分析模板：{template_path} ===\n")

    if not os.path.exists(template_path):
        print(f"文件不存在：{template_path}\n")
        return

    try:
        with zipfile.ZipFile(template_path, 'r') as zf:
            namelist = zf.namelist()

            # Find customUI files
            customui_files = [n for n in namelist if 'customUI' in n.lower()]

            if customui_files:
                print("[customUI 文件夹内容]")
                for f in customui_files:
                    print(f"  - {f}")

                print()
                print("[customUI XML 内容]")
                for f in customui_files:
                    print(f"\n--- {f} ---")
                    content = zf.read(f).decode('utf-8', errors='ignore')
                    print(content)
            else:
                print("未找到 customUI 文件夹")

            # Find VBA modules
            print()
            print("[VBA 模块]")
            vba_files = [n for n in namelist if n.lower().startswith('vba/') and n.endswith('.bas')]

            if vba_files:
                for f in vba_files:
                    print(f"\n--- {f} ---")
                    content = zf.read(f).decode('utf-8', errors='ignore')
                    print(content[:2000])  # First 2000 chars
                    if len(content) > 2000:
                        print("... (内容被截断)")
            else:
                print("未找到 VBA 模块")

            # List all files
            print()
            print("[完整文件列表]")
            for name in sorted(namelist):
                info = zf.getinfo(name)
                print(f"  {name}: {info.file_size} bytes")

    except Exception as e:
        print(f"错误：{e}")

    print()


def scan_directories():
    """Scan common directories for templates."""
    paths_to_check = [
        r'C:\Users\L\AppData\Roaming\Kingsoft\WPS Office\startup\wps',
        r'D:\WPS Office\12.1.0.25225\office6\XLSTART',
        r'D:\ScriptNexus\templates',
    ]

    all_templates = []
    for base_dir in paths_to_check:
        if not os.path.exists(base_dir):
            continue

        for f in os.listdir(base_dir):
            if f.endswith('.dotm') or f.endswith('.xlam'):
                all_templates.append({
                    'dir': base_dir,
                    'path': os.path.join(base_dir, f),
                    'name': f,
                })

    return all_templates


def main():
    """Main entry point."""
    print("=" * 70)
    print("WPS 功能区 (Ribbon) 配置提取工具")
    print("=" * 70)
    print()

    if len(sys.argv) > 1:
        # Command line mode
        template_path = sys.argv[1]
        extract_custom_ui(template_path)
    else:
        # Interactive mode
        print("扫描常用目录...\n")

        templates = scan_directories()

        if not templates:
            print("未找到模板文件!")
            return

        print(f"找到 {len(templates)} 个模板文件:\n")
        for i, tmpl in enumerate(templates, 1):
            print(f"  {i}. {tmpl['name']} ({tmpl['dir']})")

        print()
        print("-" * 70)
        print()

        for tmpl in templates:
            extract_custom_ui(tmpl['path'])


if __name__ == '__main__':
    main()
