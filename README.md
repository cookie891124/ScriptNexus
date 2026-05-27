# ScriptNexus — 办公脚本一站式管理平台 🚀

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%2B-lightgrey)]()
[![Python](https://img.shields.io/badge/python-3.10%2B-green)]()

> 🏦 诞生于**企业（）**内网环境，以 vibe coding 从零构建的 AI 辅助办公自动化工具。

简体中文 | [English](README-en.md)

---

## 📖 关于这个项目

我是一名**企业（a large enterprise / ）员工，没有技术背景**。

在 AI 快速发展的浪潮下，我开始学习 vibe coding，尝试用代码解决日常办公中的实际问题。ScriptNexus 是我学习以来完成的**第一个相对复杂的项目**——它从内网办公场景的真实需求出发，逐步迭代，最终成为覆盖 Python 脚本、WPS 宏和 Chrome JS 书签的一站式管理平台。

目前已在内网办公环境中稳定运行，确实能提升日常效率。我希望以这个项目为起点，**逐步在内网搭建一个办公自动化的生态底座**，让更多同事可以借助 AI 降低重复性劳动的门槛。

> ⚠️ 当前仅支持 Windows 系统封装。企业全面切换到麒麟系统后，我会及时适配更新。

---

## 📸 界面预览

![Dashboard](screenshots/dashboard.png)
![Python Module](screenshots/python_module.png)
![WPS Module](screenshots/wps_module.png)
![Chrome JS Module](screenshots/js_module.png)
![Settings](screenshots/settings.png)

---

## 🎯 功能特性

| 模块 | 说明 |
|------|------|
| **Python 模块** | 编写、编辑、运行 Python 脚本；支持实时交互式输入输出、多进程并行执行、依赖检测与 WHL 下载 |
| **WPS 模块** | 管理 WPS Office 宏脚本，可视化编排功能区（Ribbon）布局，一键部署 Word/Excel 模板 |
| **Chrome JS 模块** | 管理 JavaScript 书签脚本（bookmarklet），集成 Chrome 书签同步 |
| **导入/导出** | 一键打包脚本与配置为 `.snx` 文件，便于内网不同终端间迁移 |
| **系统托盘** | 最小化到托盘，右键快速访问常用功能 |

---

## 📦 系统要求

- Windows 10+
- WPS Office（WPS 模块依赖）
- Google Chrome（JS 模块依赖）
- Python 3.10+（从源码运行时需要）

---

## 🚀 快速开始

### 方式一：从源码运行

```bash
git clone https://github.com/YOUR_USERNAME/ScriptNexus.git
cd ScriptNexus
pip install -r requirements.txt
python app.py
```

### 方式二：直接使用 EXE

从 [Releases](https://github.com/YOUR_USERNAME/ScriptNexus/releases) 下载最新版 `ScriptNexus.exe`，双击运行。

---

## 📥 构建

```bash
build_windows.bat
```

产物在 `dist/ScriptNexus.exe`。

---

## 💻 开发

```bash
pip install -r requirements.txt
python app.py

# 运行测试
pytest tests/
```

---

## 🤔 常见问题

> **Q: 为什么只支持 Windows？**

A: 我所在的企业目前使用 Windows 10 企业版。全行切换到麒麟系统后，我会及时适配 Linux 版本。

> **Q: WPS 模块需要什么版本？**

A: WPS Office 12.8.2+。核心依赖 WPS 的加载项机制和 customUI 功能区配置。

> **Q: 如何在纯内网环境安装依赖？**

A: 项目的 Python 模块内置了 WHL 离线下载功能，可以在外网下载依赖包后，通过 U 盘等介质传入内网安装。

---

## 📝 许可证

MIT License — 详见 [LICENSE](LICENSE)。
