# 脚本管理器设计文档

**创建日期:** 2026-04-10  
**状态:** 已确认  
**参考项目:** CC-Switch (UI 设计参考)

---

## 1. 项目概述

### 1.1 项目目标

开发一个企业内网使用的脚本管理器，实现对 Python 脚本、WPS 脚本、网页脚本（JavaScript）的集中管理。

### 1.2 环境约束

- **网络环境:** 企业内网，不接入互联网
- **操作系统:** Windows 10 企业版
- **浏览器:** Chrome 
- **WPS:** WPS Office （加载项状态启用，但 WPS 加载项和 COM 加载项未启用）
- **Python:** 3.10.*

### 1.3 核心需求

| 模块 | 核心功能 | 部署方式 |
|------|----------|----------|
| Python 脚本 | 树状依赖图、whl 文件池、依赖检测、离线安装 | PowerShell 执行 |
| WPS 脚本 | 功能区/右键菜单映射、.dotm/.xlam 模板管理 | 自启动目录部署 |
| JS 脚本 | Chrome 书签映射 | 直接修改 Bookmarks 文件 |

---

## 2. 技术架构

### 2.1 技术选型

- **语言:** Python 3.10
- **UI 框架:** PyQt6
- **数据库:** SQLite
- **配置文件:** JSON

### 2.2 架构模式

模块化单体架构，分为三层：

```
┌─────────────────────────────────────────────────────────┐
│  UI 层 (ui/)                                             │
│  - 主窗口、导航栏、工具栏、子模块 UI、对话框             │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  服务层 (services/ + core/)                              │
│  - 业务逻辑服务、核心服务（配置、部署、导入导出）         │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  数据层 (models/)                                        │
│  - 数据模型、SQLite 数据访问                              │
└─────────────────────────────────────────────────────────┘
```

### 2.3 目录结构

```
D:\WPS-Addons\
├── app.py                          # 应用入口
├── core/                           # 核心服务层
│   ├── __init__.py
│   ├── config_service.py           # 配置管理
│   ├── deployment_service.py       # 一键部署
│   ├── import_export_service.py    # 导入导出
│   ├── path_detection_service.py   # 路径探测
│   └── event_bus.py                # 内部事件总线
├── ui/                             # UI 层
│   ├── __init__.py
│   ├── main_window.py              # 主窗口
│   ├── system_tray.py              # 系统托盘
│   ├── components/                 # 通用组件
│   │   ├── __init__.py
│   │   ├── nav_bar.py              # 左侧导航栏
│   │   ├── toolbar.py              # 顶部工具栏
│   │   └── dashboard.py            # 首页仪表盘
│   ├── modules/                    # 子模块 UI
│   │   ├── __init__.py
│   │   ├── python_module.py        # Python 脚本模块
│   │   ├── wps_module.py           # WPS 脚本模块
│   │   └── js_module.py            # JS 脚本模块
│   └── dialogs/                    # 对话框
│       ├── __init__.py
│       ├── setup_wizard.py         # 首次启动向导
│       ├── settings_dialog.py      # 设置对话框
│       └── ...
├── services/                       # 业务服务层
│   ├── __init__.py
│   ├── python_service.py           # Python 脚本管理
│   ├── wps_service.py              # WPS 模板管理
│   ├── js_service.py               # JS 书签管理
│   └── dependency_service.py       # 依赖检测服务
├── models/                         # 数据模型
│   ├── __init__.py
│   ├── script_model.py             # 脚本数据模型
│   └── repository.py               # SQLite 数据访问
├── data/                           # 数据目录
│   ├── scripts.db                  # SQLite 数据库
│   └── config.json                 # 配置文件
├── scripts/                        # 脚本存储
│   ├── python/
│   ├── wps/
│   └── javascript/
├── whl_pool/                       # Python 依赖库池
└── templates/                      # WPS 模板文件
    ├── word_template.dotm
    └── excel_template.xlam
```

---

## 3. 数据模型

### 3.1 SQLite 表结构

```sql
-- scripts 表
CREATE TABLE scripts (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,  -- 'python', 'wps', 'javascript'
    parent_id INTEGER,   -- 树状结构父节点
    code TEXT,
    description TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- dependencies 表 (Python 脚本依赖)
CREATE TABLE dependencies (
    id INTEGER PRIMARY KEY,
    script_id INTEGER,
    package_name TEXT,
    version TEXT,
    installed BOOLEAN,
    FOREIGN KEY (script_id) REFERENCES scripts(id)
);

-- wps_mappings 表
CREATE TABLE wps_mappings (
    id INTEGER PRIMARY KEY,
    script_id INTEGER,
    target_app TEXT,  -- 'word' or 'excel'
    ribbon_group TEXT,
    ribbon_label TEXT,
    context_menu_label TEXT,
    FOREIGN KEY (script_id) REFERENCES scripts(id)
);

-- js_bookmarks 表
CREATE TABLE js_bookmarks (
    id INTEGER PRIMARY KEY,
    script_id INTEGER,
    bookmark_url TEXT,
    parent_folder TEXT,
    position INTEGER,
    FOREIGN KEY (script_id) REFERENCES scripts(id)
);

-- config 表
CREATE TABLE config (
    key TEXT PRIMARY KEY,
    value TEXT
);
```

---

## 4. 核心功能设计

### 4.1 一键部署流程

```
用户点击"一键部署"
        │
        ▼
DeploymentService.deploy_all()
        │
        ├──► deploy_wps_word()
        │    - 读取所有 WPS 脚本
        │    - 生成 Ribbon XML
        │    - 生成 VBA 代码
        │    - 创建/更新 .dotm 文件
        │    - 复制到 Word 自启动目录
        │
        ├──► deploy_wps_excel()
        │    - 同上，创建 .xlam 文件
        │
        └──► deploy_chrome_bookmarks()
             - 读取所有 JS 脚本
             - 生成书签结构
             - 写入 Chrome Bookmarks 文件
```

### 4.2 导入导出流程

**导出:**
```
用户点击"导出" 
        │
        ▼
ImportExportService.export_all()
        - 打包 scripts/ 目录
        - 打包 data/config.json
        - 打包 data/scripts.db
        - 打包 templates/
        - 生成 scripts_backup_YYYYMMDD.zip
```

**导入:**
```
用户选择 ZIP 文件
        │
        ▼
ImportExportService.import_package(zip_path)
        - 解压到临时目录
        - 验证文件结构
        - 合并/覆盖配置
        - 导入数据库记录
        - 清理临时文件
```

### 4.3 WPS 模板生成流程

```
generate_word_template():
        │
        ▼
1. 创建 Word Document 对象
2. 插入 Ribbon XML 到 word/customUI/customUI.xml
3. 插入 VBA 代码到 VBA 工程模块
4. 另存为 .dotm 格式
5. 复制到 STARTUP 目录
```

### 4.4 Python 依赖检测流程

```
detect_dependencies(script_path):
        │
        ▼
1. 使用 ast 模块解析 Python 脚本
2. 提取所有 import 语句
3. 查询 SQLite dependencies 表
4. 检查 whl_pool 中是否存在
5. 标记缺失的依赖
```

---

## 5. UI 设计

### 5.1 主窗口布局

```
┌─────────────────────────────────────────────────────────┐
│  [Logo] 脚本管理器          [一键部署] [导入] [导出] [- □ ×]│
├──────────┬──────────────────────────────────────────────┤
│          │                                              │
│ 首页     │  [内容区域 - 动态切换]                        │
│ Python   │                                              │
│ WPS     │                                              │
│ JS      │                                              │
│ 设置     │                                              │
│          │                                              │
└──────────┴──────────────────────────────────────────────┘
```

### 5.2 系统托盘

- 右键菜单：打开主窗口、一键部署、退出
- 双击托盘图标打开主窗口
- 最小化到托盘（非关闭）

### 5.3 首次启动向导

- 第 1 步：欢迎页（可跳过）
- 第 2 步：路径探测（自动探测 + 手动确认/修改）
- 第 3 步：完成

---

## 6. 依赖库清单

```
# 核心
PyQt6>=6.4.0
sqlite3 (内置)

# WPS 模板操作
python-docx>=0.8.11
openpyxl>=3.0.0

# 依赖检测
ast (内置)
pip (内置)

# 打包
zipfile (内置)
json (内置)

# 可选：依赖关系图可视化
graphviz>=0.20.0
```

---

## 7. 开发计划

开发将按以下顺序进行：

1. **项目初始化** - 创建目录结构、依赖安装
2. **核心服务层** - ConfigService, PathDetectionService
3. **数据层** - Repository, 数据模型
4. **UI 框架层** - MainWindow, NavBar, SystemTray
5. **子模块开发** - PythonModule, WpsModule, JsModule
6. **部署功能** - DeploymentService
7. **导入导出功能** - ImportExportService
8. **首次启动向导** - SetupWizard
9. **集成测试与优化**

---

## 8. 风险与注意事项

1. **WPS 模板生成:** .dotm 和.xlam 是 ZIP 格式，需要正确操作内部 XML 和 VBA 工程
2. **Chrome 书签文件:** Chrome 运行时可能锁定文件，需要处理文件占用情况
3. **内网环境:** 所有依赖需要离线安装，确保 whl 文件完整
4. **VBA 代码生成:** 需要确保生成的 VBA 代码语法正确，能被 WPS 识别
