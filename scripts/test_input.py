# 测试交互式输入脚本
print("=== 交互式输入测试 ===")
print()

# 测试简单输入
name = input("请输入您的名字: ")
print(f"您好，{name}！")

# 测试选择输入
choice = input("请选择操作 (1/2/3): ")
if choice == "1":
    print("选择了操作 1")
elif choice == "2":
    print("选择了操作 2")
elif choice == "3":
    print("选择了操作 3")
else:
    print("无效选择")

# 测试确认输入
confirm = input("是否继续？(y/n): ")
if confirm.lower() == 'y':
    print("继续执行...")
    age = input("请输入年龄: ")
    print(f"年龄: {age}")
else:
    print("已取消")

print()
print("=== 测试完成 ===")
