"""检查生成的 VBA 模板文件结构"""
import zipfile
import os
import glob
import sys

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def check_template_structure(template_path):
    """检查模板文件的 VBA 结构"""
    print(f"\n{'='*60}")
    print(f"检查文件：{os.path.basename(template_path)}")
    print(f"{'='*60}")

    if not os.path.exists(template_path):
        print(f"文件不存在：{template_path}")
        return

    with zipfile.ZipFile(template_path, 'r') as zf:
        # 显示所有文件
        print("\n📁 文件结构:")
        for name in sorted(zf.namelist()):
            marker = "← VBA 文件" if 'VBA' in name.upper() else ""
            print(f"  {name} {marker}")

        # 检查 VBA 相关内容
        vba_files = [n for n in zf.namelist() if 'VBA' in n.upper()]

        if not vba_files:
            print("\n⚠️  警告：未找到 VBA 相关文件！")
            return

        print(f"\n✅ 找到 {len(vba_files)} 个 VBA 相关文件")

        # 读取并显示 .bas 文件内容
        bas_files = [f for f in vba_files if f.endswith('.bas')]
        if bas_files:
            print(f"\n📄 VBA 代码内容 ({bas_files[0]}):")
            print("-"*40)
            content = zf.read(bas_files[0]).decode('utf-8')
            lines = content.split('\n')
            for i, line in enumerate(lines[:40]):  # 显示前 40 行
                print(f"  {line}")
            if len(lines) > 40:
                print(f"  ... 还有 {len(lines)-40} 行")

        # 检查元数据文件
        for meta_file in ['_VBA_PROJECT', 'dir']:
            full_path = None
            for f in vba_files:
                if f.endswith(meta_file):
                    full_path = f
                    break
            if full_path:
                print(f"\n📄 {meta_file} 内容:")
                print("-"*40)
                try:
                    content = zf.read(full_path).decode('utf-8')
                    print(content)
                except Exception as e:
                    print(f"读取失败：{e}")

        # 检查 Content_Types
        if '[Content_Types].xml' in zf.namelist():
            content = zf.read('[Content_Types].xml').decode('utf-8')
            has_vba = 'vba' in content.lower()
            print(f"\n📄 [Content_Types].xml: {'包含 VBA 类型' if has_vba else '⚠️ 不包含 VBA 类型'}")

# 查找并检查模板文件
print("🔍 正在查找 WPS 模板文件...")

# Word 模板
word_paths = [
    glob.glob(r"D:\用户\AppData\Roaming\Kingsoft\WPS Office\*\addons\WpsScriptManager_Word_*.dotm"),
    glob.glob(r"C:\Users\L\AppData\Roaming\Kingsoft\WPS Office\*\addons\WpsScriptManager_Word_*.dotm"),
]
word_files = []
for p in word_paths:
    word_files.extend(p)

# Excel 模板
excel_paths = [
    glob.glob(r"D:\用户\AppData\Roaming\Kingsoft\WPS Office\*\addons\WpsScriptManager_Excel_*.xlam"),
    glob.glob(r"C:\Users\L\AppData\Roaming\Kingsoft\WPS Office\*\addons\WpsScriptManager_Excel_*.xlam"),
]
excel_files = []
for p in excel_paths:
    excel_files.extend(p)

if word_files:
    check_template_structure(word_files[-1])
else:
    print("\n⚠️  未找到 Word 模板文件")

if excel_files:
    check_template_structure(excel_files[-1])
else:
    print("\n⚠️  未找到 Excel 模板文件")

print("\n" + "="*60)
print("检查完成")
print("="*60)
