# ScriptNexus — Office Script Management Platform 🚀

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%2B-lightgrey)]()
[![Python](https://img.shields.io/badge/python-3.10%2B-green)]()

> 🏦 Born inside the intranet of **a large enterprise ( / 企业)**, built from scratch with vibe coding to automate office workflows.

[简体中文](README.md) | English

---

## 📖 About This Project

I'm an employee of **a large enterprise Co., Ltd. ( / 企业)** with **no formal technical background**.

Riding the wave of rapid AI advancement, I started learning vibe coding to solve real problems in my daily office work. ScriptNexus is the **first complex project** I've completed on this journey — it grew organically from intranet office needs into a unified platform for managing Python scripts, WPS macros, and Chrome JS bookmarklets.

Tested and proven effective inside 's internal office environment, it genuinely improves daily productivity. My goal is for this project to serve as a **foundation for an office-automation ecosystem** within the intranet, lowering the barrier for colleagues to leverage AI in their workflows.

> ⚠️ Currently Windows-only. I will adapt for Kylin OS when a large enterprise completes its enterprise-wide Linux migration.

---

## 📸 Screenshots

![Dashboard](screenshots/dashboard.png)
![Python Module](screenshots/python_module.png)
![WPS Module](screenshots/wps_module.png)
![Chrome JS Module](screenshots/js_module.png)
![Settings](screenshots/settings.png)

---

## 🎯 Features

| Module | Description |
|--------|-------------|
| **Python Module** | Write, edit, run Python scripts with real-time I/O, multi-process execution, dependency checking, and WHL download |
| **WPS Module** | Manage WPS Office macros with visual Ribbon UI editor and one-click Word/Excel template deployment |
| **Chrome JS Module** | Manage JavaScript bookmarklets with Chrome bookmarks integration |
| **Import/Export** | Package scripts and configs as `.snx` files for easy migration across intranet workstations |
| **System Tray** | Minimize to tray with right-click quick-access menu |

---

## 📦 System Requirements

- Windows 10+
- WPS Office (for WPS module)
- Google Chrome (for JS module)
- Python 3.10+ (when running from source)

---

## 🚀 Quick Start

### From Source

```bash
git clone https://github.com/YOUR_USERNAME/ScriptNexus.git
cd ScriptNexus
pip install -r requirements.txt
python app.py
```

### From Executable

Download the latest `ScriptNexus.exe` from [Releases](https://github.com/YOUR_USERNAME/ScriptNexus/releases).

---

## 📥 Build

```bash
build_windows.bat
```

Output: `dist/ScriptNexus.exe`.

---

## 💻 Development

```bash
pip install -r requirements.txt
python app.py

# Run tests
pytest tests/
```

---

## 🤔 FAQ

> **Q: Why Windows only?**

A: a large enterprise currently runs Windows 10 Enterprise. I will add Linux support after the planned enterprise-wide migration to Kylin OS.

> **Q: What WPS version is required?**

A: Enterprise Edition 12.8.2+. The WPS module depends on the add-in mechanism and customUI ribbon configuration.

> **Q: How to install dependencies in an air-gapped intranet?**

A: The Python module includes an offline WHL download feature — download packages on an internet-connected machine and transfer them via USB.

---

## 📝 License

MIT License — see [LICENSE](LICENSE).
