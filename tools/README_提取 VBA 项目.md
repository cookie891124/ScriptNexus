# VBA 项目提取工具使用说明

## 用途

从 WPS Office 宏启用模板文件（.xlsm, .xlam, .dotm, .docm）中提取 vbaProject.bin 文件。

## 使用场景

在内网环境中，您已经有通过自定义功能区并粘贴宏命令代码创建好的可用的.xlam 和.dotm 文件，但这些文件无法直接发送到开发机。使用此脚本可以在内网环境中提取 vbaProject.bin 文件，然后将其转移到开发机用于部署。

## 使用方法

### 方法 1：提取单个文件

```bash
# 提取 Excel 模板
python extract_vba_project.py path\to\template.xlam

# 提取 Word 模板
python extract_vba_project.py path\to\template.dotm

# 指定输出目录
python extract_vba_project.py path\to\template.xlam D:\output
```

### 方法 2：批量提取整个目录

```bash
# 提取目录中所有模板文件
python extract_vba_project.py path\to\templates\directory
```

### 方法 3：交互式模式（自动扫描常用目录）

```bash
# 不提供参数，自动扫描 WPS 常用启动目录
python extract_vba_project.py
```

## 输出文件

提取成功后，会生成以下格式的文件：
- `template_name_vbaProject.bin`（Excel 和 Word 模板使用相同格式）

## 后续步骤

1. 将提取的 vbaProject.bin 文件复制到开发机
2. 重命名文件：
   - Excel 模板：`vbaProject_excel.bin`
   - Word 模板：`vbaProject_word.bin`
3. 将文件放置到部署模板目录：
   ```
   D:\WPS-Addons\templates\
   ```
4. 重新运行一键部署功能

## 支持的模板类型

| 扩展名 | 文件类型 | VBA 路径 |
|--------|----------|----------|
| .xlsm | Excel 宏启用工作簿 | xl/vbaProject.bin |
| .xlam | Excel 加载项 | xl/vbaProject.bin |
| .dotm | Word 宏启用模板 | word/vbaProject.bin |
| .docm | Word 宏启用文档 | word/vbaProject.bin |

## 常见问题

### 错误：vbaProject.bin not found in archive

此文件可能不包含 VBA 宏，或者 VBA 项目尚未初始化。请先使用 WPS VBA 编辑器添加宏到文件中。

### 错误：File not found: xxx

检查文件路径是否正确，确保文件存在于指定位置。

### 错误：is not a valid ZIP file

Office 文件应为 ZIP 压缩包格式。此文件可能已损坏，或者是旧的二进制格式（.xls, .doc 而不是.xlsm, .dotm）。

## 技术要求

- Python 3.6+
- 无需额外依赖（仅使用标准库）
