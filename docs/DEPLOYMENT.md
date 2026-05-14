# WPS 模板部署方案

## 问题

内网环境没有安装 `pywin32`，无法使用 COM 自动化注入 VBA 代码。

## 解决方案

### 方案 A：安装 pywin32（推荐，完全自动化）

在内网环境中安装 pywin32：

1. **在开发机下载 whl 文件**：
   ```bash
   pip download pywin32==310 -d D:\ScriptNexus\whl_pool
   ```

2. **复制 whl 文件到内网**

3. **在内网安装**：
   ```bash
   pip install pywin32‑310‑cp310‑cp310‑win_amd64.whl
   ```

安装后，一键部署会自动使用 COM 注入 VBA 代码。

### 方案 B：纯 Python 方案（无需 pywin32）

原理：使用预生成的 vbaProject.bin 文件注入到模板中。

**操作步骤**：

1. **在内网手动创建种子文件**：
   - 打开 WPS（WPS Office）
   - 创建 Excel 文件，按 Alt+F11 添加任意 VBA 宏
   - 保存为 `.xlam` 文件（如 `seed_excel.xlam`）
   - 创建 Word 文件，按 Alt+F11 添加任意 VBA 宏
   - 保存为 `.dotm` 文件（如 `seed_word.dotm`）

2. **提取 vbaProject.bin**：
   ```bash
   # 在内网运行
   cd D:\ScriptNexus
   python tools/extract_vba.py seed_excel.xlam templates/
   python tools/extract_vba.py seed_word.dotm templates/
   ```

3. **复制 templates 目录到开发机**（如果需要）

4. **运行部署**：
   - 程序会自动将 vbaProject.bin 注入到生成的模板文件中
   - 生成的模板文件包含 VBA 项目，WPS 启动时自动加载

## 两种方案对比

| 特性 | 方案 A (COM) | 方案 B (vbaProject.bin) |
|------|-------------|------------------------|
| 依赖 | pywin32 | 无 |
| VBA 代码 | 动态生成注入 | 预置在种子文件中 |
| 自动化程度 | 完全自动 | 需要手动准备种子文件 |
| 部署后效果 | 模板包含实际 VBA 代码 | 模板包含种子文件的 VBA 代码 |

## 说明

- **方案 A**：VBA 代码动态注入，模板包含实际脚本代码
- **方案 B**：需要提前准备一个包含 VBA 的种子文件，注入后模板包含种子的 VBA 项目

**建议**：
- 如果可以安装 pywin32，使用方案 A
- 如果无法安装 pywin32，使用方案 B（需要用户手动在 WPS 中导入一次实际的 VBA 代码）

