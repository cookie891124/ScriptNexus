"""COM VBA 注入测试工具

在内网环境中运行此脚本，测试 WPS 的 COM VBA 注入功能是否可用。
"""

import sys

def test_excel_com():
    """测试 Excel (Ket.Application) 的 COM VBA 注入。"""
    print("\n=== 测试 Excel COM VBA 注入 ===")

    try:
        import win32com.client
        print("[1] 导入 win32com.client: 成功")
    except ImportError as e:
        print(f"[1] 导入 win32com.client: 失败 - {e}")
        return False

    try:
        # 尝试连接已运行的实例
        try:
            et = win32com.client.GetActiveObject('Ket.Application')
            print("[2] 连接已运行的 WPS Excel: 成功")
        except:
            et = win32com.client.Dispatch('Ket.Application')
            print("[2] 启动新的 WPS Excel 实例：成功")

        et.Visible = False
        print("[3] 设置 Visible=False: 成功")

        wb = et.Workbooks.Add()
        print("[4] 创建工作簿：成功")

        vb_project = wb.VBProject
        print("[5] 访问 VBProject: 成功")

        # 尝试注入代码
        test_code = """Sub TestMacro()
    MsgBox "VBA 注入测试成功"
End Sub
"""
        try:
            vb_component = vb_project.VBComponents.Item('ThisWorkbook')
            vb_component.CodeModule.AddLines(test_code)
            print("[6] 注入 VBA 代码到 ThisWorkbook: 成功")
        except Exception as e:
            vb_component = vb_project.VBComponents.Add(1)
            vb_component.CodeModule.AddLines(test_code)
            print(f"[6] 注入 VBA 代码到新模块：成功 - {e}")

        # 保存测试
        import os
        test_path = os.path.join(os.path.dirname(__file__), 'test_vba_injection.xlam')
        wb.SaveAs(test_path, 52)
        print(f"[7] 保存为 .xlam: 成功 - {test_path}")

        wb.Close(False)
        et.Quit()
        print("[8] 关闭 WPS Excel: 成功")

        # 检查文件
        if os.path.exists(test_path):
            size = os.path.getsize(test_path)
            print(f"\n✅ COM VBA 注入测试成功！")
            print(f"   生成文件：{test_path}")
            print(f"   文件大小：{size} bytes")

            # 清理测试文件
            try:
                os.remove(test_path)
                print(f"   测试文件已清理")
            except:
                pass

            return True
        else:
            print(f"\n❌ 保存的文件不存在")
            return False

    except Exception as e:
        print(f"\n❌ COM VBA 注入测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def test_word_com():
    """测试 Word (Kwps.Application) 的 COM VBA 注入。"""
    print("\n=== 测试 Word COM VBA 注入 ===")

    try:
        import win32com.client
        print("[1] 导入 win32com.client: 成功")
    except ImportError as e:
        print(f"[1] 导入 win32com.client: 失败 - {e}")
        return False

    try:
        # 尝试连接已运行的实例
        try:
            word = win32com.client.GetActiveObject('Kwps.Application')
            print("[2] 连接已运行的 WPS Word: 成功")
        except:
            word = win32com.client.Dispatch('Kwps.Application')
            print("[2] 启动新的 WPS Word 实例：成功")

        word.Visible = False
        print("[3] 设置 Visible=False: 成功")

        doc = word.Documents.Add()
        print("[4] 创建文档：成功")

        vb_project = doc.VBProject
        print("[5] 访问 VBProject: 成功")

        # 尝试注入代码
        test_code = """Sub TestMacro()
    MsgBox "VBA 注入测试成功"
End Sub
"""
        try:
            vb_component = vb_project.VBComponents.Item('ThisDocument')
            vb_component.CodeModule.AddLines(test_code)
            print("[6] 注入 VBA 代码到 ThisDocument: 成功")
        except Exception as e:
            vb_component = vb_project.VBComponents.Add(1)
            vb_component.CodeModule.AddLines(test_code)
            print(f"[6] 注入 VBA 代码到新模块：成功 - {e}")

        # 保存测试
        import os
        test_path = os.path.join(os.path.dirname(__file__), 'test_vba_injection.dotm')
        doc.SaveAs(test_path, 5)
        print(f"[7] 保存为 .dotm: 成功 - {test_path}")

        doc.Close(False)
        word.Quit()
        print("[8] 关闭 WPS Word: 成功")

        # 检查文件
        if os.path.exists(test_path):
            size = os.path.getsize(test_path)
            print(f"\n✅ Word COM VBA 注入测试成功！")
            print(f"   生成文件：{test_path}")
            print(f"   文件大小：{size} bytes")

            # 清理测试文件
            try:
                os.remove(test_path)
                print(f"   测试文件已清理")
            except:
                pass

            return True
        else:
            print(f"\n❌ 保存的文件不存在")
            return False

    except Exception as e:
        print(f"\n❌ Word COM VBA 注入测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("=" * 50)
    print("WPS COM VBA 注入测试工具")
    print("=" * 50)

    excel_ok = test_excel_com()
    word_ok = test_word_com()

    print("\n" + "=" * 50)
    print("测试结果汇总:")
    print(f"  Excel COM VBA 注入：{'✅ 可用' if excel_ok else '❌ 不可用'}")
    print(f"  Word COM VBA 注入：{'✅ 可用' if word_ok else '❌ 不可用'}")
    print("=" * 50)

    if excel_ok and word_ok:
        print("\n✅ 您的内网 WPS 环境支持 COM VBA 注入！")
        print("   一键部署功能将自动注入 VBA 代码到模板文件。")
        sys.exit(0)
    else:
        print("\n⚠️  COM VBA 注入不可用，将回退到 .bas 文件方案。")
        print("   可能原因:")
        print("   1. WPS 未安装 VBA 组件")
        print("   2. WPS 安全设置限制了 VBProject 访问")
        print("   3. pywin32 版本不兼容")
        sys.exit(1)
