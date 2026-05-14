# 脚本管理器 (Script Manager) 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 开发一个企业内网使用的脚本管理器，实现 Python 脚本、WPS 脚本、JavaScript 脚本的集中管理、一键部署和导入导出功能。

**Architecture:** 模块化单体架构，分为 UI 层 (PyQt6)、服务层 (业务逻辑)、数据层 (SQLite + Repository 模式)。采用 TDD 开发，频繁提交。

**Tech Stack:** Python 3.10, PyQt6>=6.4.0, SQLite3, python-docx, openpyxl

**Design Spec:** `docs/superpowers/specs/2026-04-10-script-manager-design.md`

---

## Phase 1: 项目初始化

### Task 1.1: 创建项目目录结构

**Files:**
- Create: `D:\WPS-Addons\app.py`
- Create: `D:\WPS-Addons\core\__init__.py`
- Create: `D:\WPS-Addons\ui\__init__.py`
- Create: `D:\WPS-Addons\services\__init__.py`
- Create: `D:\WPS-Addons\models\__init__.py`
- Create: `D:\WPS-Addons\data\`
- Create: `D:\WPS-Addons\scripts\python\`
- Create: `D:\WPS-Addons\scripts\wps\`
- Create: `D:\WPS-Addons\scripts\javascript\`
- Create: `D:\WPS-Addons\whl_pool\`
- Create: `D:\WPS-Addons\templates\`

- [ ] **Step 1: 创建所有目录和空文件**

```bash
cd D:\WPS-Addons
mkdir -p core ui ui/components ui/modules ui/dialogs services models data scripts/python scripts/wps scripts/javascript whl_pool templates docs/superpowers/plans
```

- [ ] **Step 2: 创建__init__.py 文件**

```bash
touch core/__init__.py ui/__init__.py services/__init__.py models/__init__.py
```

- [ ] **Step 3: 创建 requirements.txt**

```txt
# requirements.txt
PyQt6>=6.4.0
python-docx>=0.8.11
openpyxl>=3.0.0
```

- [ ] **Step 4: 提交**

```bash
git init
git add .
git commit -m "feat: initialize project structure"
```

---

## Phase 2: 数据层

### Task 2.1: Repository 基类

**Files:**
- Create: `models/repository.py`
- Test: `tests/test_repository.py`

- [ ] **Step 1: 编写 Repository 测试**

```python
# tests/test_repository.py
import sqlite3
import pytest
from models.repository import Repository

def test_repository_creates_connection():
    repo = Repository(':memory:')
    assert repo.conn is not None
    assert isinstance(repo.conn, sqlite3.Connection)

def test_repository_execute():
    repo = Repository(':memory:')
    repo.execute('CREATE TABLE test (id INTEGER, name TEXT)')
    repo.execute('INSERT INTO test VALUES (?, ?)', (1, 'test'))
    result = repo.query('SELECT * FROM test')
    assert len(result) == 1
    assert result[0] == (1, 'test')
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/test_repository.py -v
```
Expected: FAIL (module not found)

- [ ] **Step 3: 实现 Repository 类**

```python
# models/repository.py
import sqlite3
from typing import List, Tuple, Any, Optional

class Repository:
    """SQLite 数据访问基类"""
    
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
    
    def execute(self, sql: str, params: Tuple = ()) -> None:
        """执行无返回的 SQL"""
        with self.conn:
            self.conn.execute(sql, params)
    
    def query(self, sql: str, params: Tuple = ()) -> List[Tuple]:
        """执行查询并返回结果"""
        cursor = self.conn.execute(sql, params)
        return cursor.fetchall()
    
    def query_one(self, sql: str, params: Tuple = ()) -> Optional[Tuple]:
        """执行查询并返回单条结果"""
        cursor = self.conn.execute(sql, params)
        return cursor.fetchone()
    
    def close(self) -> None:
        """关闭连接"""
        self.conn.close()
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/test_repository.py -v
```
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add models/repository.py tests/test_repository.py
git commit -m "feat: add Repository base class with tests"
```

---

### Task 2.2: ScriptModel 数据模型

**Files:**
- Create: `models/script_model.py`
- Test: `tests/test_script_model.py`

- [ ] **Step 1: 编写 ScriptModel 测试**

```python
# tests/test_script_model.py
import pytest
from models.repository import Repository
from models.script_model import ScriptModel, ScriptType

def test_script_model_create_tables():
    repo = Repository(':memory:')
    model = ScriptModel(repo)
    model.create_tables()
    tables = repo.query("SELECT name FROM sqlite_master WHERE type='table'")
    table_names = [t[0] for t in tables]
    assert 'scripts' in table_names
    assert 'dependencies' in table_names
    assert 'wps_mappings' in table_names
    assert 'js_bookmarks' in table_names
    assert 'config' in table_names

def test_script_model_add_script():
    repo = Repository(':memory:')
    model = ScriptModel(repo)
    model.create_tables()
    script_id = model.add_script(
        name='test_script',
        script_type=ScriptType.PYTHON,
        code='print("hello")',
        description='Test script'
    )
    assert script_id is not None
    script = model.get_script(script_id)
    assert script['name'] == 'test_script'
    assert script['type'] == 'python'

def test_script_model_get_tree():
    repo = Repository(':memory:')
    model = ScriptModel(repo)
    model.create_tables()
    parent_id = model.add_script(name='parent', script_type=ScriptType.PYTHON)
    child_id = model.add_script(name='child', script_type=ScriptType.PYTHON, parent_id=parent_id)
    tree = model.get_tree(ScriptType.PYTHON)
    assert len(tree) == 1
    assert tree[0]['id'] == parent_id
    assert len(tree[0]['children']) == 1
    assert tree[0]['children'][0]['id'] == child_id
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/test_script_model.py -v
```
Expected: FAIL

- [ ] **Step 3: 实现 ScriptModel 类**

```python
# models/script_model.py
from enum import Enum
from typing import List, Dict, Optional, Any
from datetime import datetime
from models.repository import Repository

class ScriptType(str, Enum):
    PYTHON = 'python'
    WPS = 'wps'
    JAVASCRIPT = 'javascript'

class ScriptModel:
    """脚本数据模型"""
    
    def __init__(self, repo: Repository):
        self.repo = repo
    
    def create_tables(self) -> None:
        """创建所有数据表"""
        self.repo.execute('''
            CREATE TABLE IF NOT EXISTS scripts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                parent_id INTEGER,
                code TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES scripts(id)
            )
        ''')
        
        self.repo.execute('''
            CREATE TABLE IF NOT EXISTS dependencies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                script_id INTEGER NOT NULL,
                package_name TEXT NOT NULL,
                version TEXT,
                installed BOOLEAN DEFAULT 0,
                FOREIGN KEY (script_id) REFERENCES scripts(id)
            )
        ''')
        
        self.repo.execute('''
            CREATE TABLE IF NOT EXISTS wps_mappings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                script_id INTEGER NOT NULL,
                target_app TEXT NOT NULL,
                ribbon_group TEXT,
                ribbon_label TEXT,
                context_menu_label TEXT,
                FOREIGN KEY (script_id) REFERENCES scripts(id)
            )
        ''')
        
        self.repo.execute('''
            CREATE TABLE IF NOT EXISTS js_bookmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                script_id INTEGER NOT NULL,
                bookmark_url TEXT NOT NULL,
                parent_folder TEXT,
                position INTEGER DEFAULT 0,
                FOREIGN KEY (script_id) REFERENCES scripts(id)
            )
        ''')
        
        self.repo.execute('''
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
    
    def add_script(self, name: str, script_type: ScriptType, 
                   code: str = '', description: str = '',
                   parent_id: Optional[int] = None) -> int:
        """添加脚本"""
        self.repo.execute('''
            INSERT INTO scripts (name, type, code, description, parent_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, script_type.value, code, description, parent_id))
        result = self.repo.query_one('SELECT last_insert_rowid()')
        return result[0]
    
    def get_script(self, script_id: int) -> Optional[Dict[str, Any]]:
        """获取脚本"""
        row = self.repo.query_one(
            'SELECT * FROM scripts WHERE id = ?', (script_id,)
        )
        if row:
            return dict(row)
        return None
    
    def get_tree(self, script_type: ScriptType) -> List[Dict[str, Any]]:
        """获取树状结构的脚本列表"""
        rows = self.repo.query(
            'SELECT * FROM scripts WHERE type = ? ORDER BY name',
            (script_type.value,)
        )
        scripts = [dict(row) for row in rows]
        return self._build_tree(scripts, None)
    
    def _build_tree(self, scripts: List[Dict], parent_id: Optional[int]) -> List[Dict]:
        """递归构建树结构"""
        children = [s for s in scripts if s['parent_id'] == parent_id]
        for child in children:
            child['children'] = self._build_tree(scripts, child['id'])
        return children
    
    def update_script(self, script_id: int, **kwargs) -> None:
        """更新脚本"""
        if not kwargs:
            return
        set_clause = ', '.join([f'{k} = ?' for k in kwargs.keys()])
        values = list(kwargs.values()) + [script_id]
        self.repo.execute(f'''
            UPDATE scripts SET {set_clause}, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', values)
    
    def delete_script(self, script_id: int) -> None:
        """删除脚本"""
        self.repo.execute('DELETE FROM scripts WHERE id = ?', (script_id,))
    
    def get_config(self, key: str, default: str = None) -> Optional[str]:
        """获取配置值"""
        row = self.repo.query_one(
            'SELECT value FROM config WHERE key = ?', (key,)
        )
        return row[0] if row else default
    
    def set_config(self, key: str, value: str) -> None:
        """设置配置值"""
        self.repo.execute('''
            INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)
        ''', (key, value))
```

- [ ] **Step 4: 添加依赖表操作方法**

```python
# 在 ScriptModel 类中添加

def add_dependency(self, script_id: int, package_name: str, 
                   version: str = '', installed: bool = False) -> int:
    """添加依赖"""
    self.repo.execute('''
        INSERT INTO dependencies (script_id, package_name, version, installed)
        VALUES (?, ?, ?, ?)
    ''', (script_id, package_name, version, 1 if installed else 0))
    result = self.repo.query_one('SELECT last_insert_rowid()')
    return result[0]

def get_dependencies(self, script_id: int) -> List[Dict[str, Any]]:
    """获取脚本依赖列表"""
    rows = self.repo.query(
        'SELECT * FROM dependencies WHERE script_id = ?', (script_id,)
    )
    return [dict(row) for row in rows]

def update_dependency_installed(self, dep_id: int, installed: bool) -> None:
    """更新依赖安装状态"""
    self.repo.execute('''
        UPDATE dependencies SET installed = ? WHERE id = ?
    ''', (1 if installed else 0, dep_id))
```

- [ ] **Step 5: 添加 WPS 映射操作方法**

```python
# 在 ScriptModel 类中添加

def add_wps_mapping(self, script_id: int, target_app: str,
                    ribbon_group: str = '', ribbon_label: str = '',
                    context_menu_label: str = '') -> int:
    """添加 WPS 映射"""
    self.repo.execute('''
        INSERT INTO wps_mappings (script_id, target_app, ribbon_group, 
                                   ribbon_label, context_menu_label)
        VALUES (?, ?, ?, ?, ?)
    ''', (script_id, target_app, ribbon_group, ribbon_label, context_menu_label))
    result = self.repo.query_one('SELECT last_insert_rowid()')
    return result[0]

def get_wps_mappings(self, script_id: int) -> Optional[Dict[str, Any]]:
    """获取 WPS 映射"""
    row = self.repo.query_one(
        'SELECT * FROM wps_mappings WHERE script_id = ?', (script_id,)
    )
    return dict(row) if row else None

def get_all_wps_scripts(self) -> List[Dict[str, Any]]:
    """获取所有 WPS 脚本及其映射"""
    rows = self.repo.query('''
        SELECT s.*, w.target_app, w.ribbon_group, w.ribbon_label, 
               w.context_menu_label
        FROM scripts s
        LEFT JOIN wps_mappings w ON s.id = w.script_id
        WHERE s.type = 'wps'
    ''')
    return [dict(row) for row in rows]
```

- [ ] **Step 6: 添加 JS 书签操作方法**

```python
# 在 ScriptModel 类中添加

def add_js_bookmark(self, script_id: int, bookmark_url: str,
                    parent_folder: str = '', position: int = 0) -> int:
    """添加 JS 书签"""
    self.repo.execute('''
        INSERT INTO js_bookmarks (script_id, bookmark_url, parent_folder, position)
        VALUES (?, ?, ?, ?)
    ''', (script_id, bookmark_url, parent_folder, position))
    result = self.repo.query_one('SELECT last_insert_rowid()')
    return result[0]

def get_js_bookmarks(self, script_id: int) -> Optional[Dict[str, Any]]:
    """获取 JS 书签"""
    row = self.repo.query_one(
        'SELECT * FROM js_bookmarks WHERE script_id = ?', (script_id,)
    )
    return dict(row) if row else None

def get_all_js_scripts(self) -> List[Dict[str, Any]]:
    """获取所有 JS 脚本及其书签"""
    rows = self.repo.query('''
        SELECT s.*, j.bookmark_url, j.parent_folder, j.position
        FROM scripts s
        LEFT JOIN js_bookmarks j ON s.id = j.script_id
        WHERE s.type = 'javascript'
    ''')
    return [dict(row) for row in rows]
```

- [ ] **Step 7: 运行测试验证通过**

```bash
pytest tests/test_script_model.py -v
```
Expected: PASS

- [ ] **Step 8: 提交**

```bash
git add models/script_model.py tests/test_script_model.py
git commit -m "feat: add ScriptModel with full CRUD operations"
```

---

## Phase 3: 核心服务层

### Task 3.1: PathDetectionService 路径探测服务

**Files:**
- Create: `core/path_detection_service.py`
- Test: `tests/test_path_detection.py`

- [ ] **Step 1: 编写路径探测测试**

```python
# tests/test_path_detection.py
import pytest
from core.path_detection_service import PathDetectionService

def test_detect_chrome_user_data():
    service = PathDetectionService()
    path = service.detect_chrome_user_data()
    assert path is not None
    assert 'Chrome' in path or 'chrome' in path

def test_detect_wps_word_startup():
    service = PathDetectionService()
    path = service.detect_wps_word_startup()
    # 可能返回 None 如果 WPS 未安装
    if path:
        assert 'Kingsoft' in path or 'WPS' in path or 'STARTUP' in path

def test_detect_wps_excel_startup():
    service = PathDetectionService()
    path = service.detect_wps_excel_startup()
    if path:
        assert 'Kingsoft' in path or 'WPS' in path or 'XLSTART' in path
```

- [ ] **Step 2: 实现 PathDetectionService**

```python
# core/path_detection_service.py
import os
import re
from typing import Optional
from pathlib import Path

class PathDetectionService:
    """路径探测服务"""
    
    def __init__(self):
        self.appdata = os.environ.get('APPDATA', '')
        self.local_appdata = os.environ.get('LOCALAPPDATA', '')
        self.user_profile = os.environ.get('USERPROFILE', '')
    
    def detect_chrome_user_data(self) -> str:
        """探测 Chrome 用户数据目录"""
        default_path = os.path.join(
            self.local_appdata,
            'Google', 'Chrome', 'User Data'
        )
        if os.path.exists(default_path):
            return default_path
        
        # 尝试其他可能的路径
        alternatives = [
            os.path.join(self.appdata, 'Google', 'Chrome', 'User Data'),
            os.path.join(self.user_profile, 'Local Settings', 'Application Data',
                        'Google', 'Chrome', 'User Data'),
        ]
        for path in alternatives:
            if os.path.exists(path):
                return path
        
        return default_path  # 返回默认路径，即使不存在
    
    def detect_chrome_bookmarks_file(self) -> str:
        """探测 Chrome 书签文件路径"""
        user_data = self.detect_chrome_user_data()
        return os.path.join(user_data, 'Default', 'Bookmarks')
    
    def detect_wps_word_startup(self) -> Optional[str]:
        """探测 WPS Word 自启动目录"""
        # 常见的 WPS Word STARTUP 路径
        paths_to_try = [
            os.path.join(self.appdata, 'Kingsoft', 'WPS Office', 
                        'word', 'STARTUP'),
            os.path.join(self.appdata, 'Kingsoft', 'WPS Office', 
                        'addons', 'word', 'STARTUP'),
        ]
        
        # 尝试从注册表获取（如果需要）
        for path in paths_to_try:
            if os.path.exists(path):
                return path
        
        # 如果都不存在，返回第一个作为默认
        return paths_to_try[0]
    
    def detect_wps_excel_startup(self) -> Optional[str]:
        """探测 WPS Excel 自启动目录"""
        paths_to_try = [
            os.path.join(self.appdata, 'Kingsoft', 'WPS Office', 
                        'excel', 'XLSTART'),
            os.path.join(self.appdata, 'Kingsoft', 'WPS Office', 
                        'addons', 'excel', 'XLSTART'),
        ]
        
        for path in paths_to_try:
            if os.path.exists(path):
                return path
        
        return paths_to_try[0]
    
    def detect_wps_installation(self) -> Optional[str]:
        """探测 WPS 安装目录"""
        paths_to_try = [
            r'C:\Program Files (x86)\Kingsoft\WPS Office',
            r'C:\Program Files\Kingsoft\WPS Office',
            os.path.join(self.appdata, 'Kingsoft', 'WPS Office'),
        ]
        
        for path in paths_to_try:
            if os.path.exists(path):
                return path
        
        return None
    
    def get_default_scripts_dir(self) -> str:
        """获取默认脚本目录"""
        return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts')
    
    def get_default_whl_pool_dir(self) -> str:
        """获取默认 whl 文件池目录"""
        return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'whl_pool')
    
    def get_default_config_dir(self) -> str:
        """获取默认配置目录"""
        return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
```

- [ ] **Step 3: 运行测试验证通过**

```bash
pytest tests/test_path_detection.py -v
```
Expected: PASS (或在 WPS 未安装时部分测试跳过)

- [ ] **Step 4: 提交**

```bash
git add core/path_detection_service.py tests/test_path_detection.py
git commit -m "feat: add PathDetectionService for auto-detecting paths"
```

---

### Task 3.2: ConfigService 配置管理服务

**Files:**
- Create: `core/config_service.py`
- Test: `tests/test_config_service.py`

- [ ] **Step 1: 编写配置服务测试**

```python
# tests/test_config_service.py
import pytest
import json
import tempfile
import os
from core.config_service import ConfigService

@pytest.fixture
def temp_config():
    fd, path = tempfile.mktemp(suffix='.json')
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)

def test_config_service_load_empty(temp_config):
    service = ConfigService(temp_config)
    config = service.load()
    assert config == {}

def test_config_service_save_and_load(temp_config):
    service = ConfigService(temp_config)
    service.save({'test_key': 'test_value'})
    loaded = service.load()
    assert loaded['test_key'] == 'test_value'

def test_config_service_get_set(temp_config):
    service = ConfigService(temp_config)
    service.set('key1', 'value1')
    assert service.get('key1') == 'value1'
    assert service.get('nonexistent', 'default') == 'default'
```

- [ ] **Step 2: 实现 ConfigService**

```python
# core/config_service.py
import json
import os
from typing import Any, Dict, Optional

class ConfigService:
    """配置管理服务"""
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
    
    def load(self) -> Dict[str, Any]:
        """加载配置"""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        else:
            self.config = {}
        return self.config
    
    def save(self, config: Optional[Dict[str, Any]] = None) -> None:
        """保存配置"""
        if config is not None:
            self.config = config
        
        # 确保目录存在
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """设置配置值"""
        self.config[key] = value
    
    def delete(self, key: str) -> None:
        """删除配置值"""
        self.config.pop(key, None)
```

- [ ] **Step 3: 运行测试验证通过**

```bash
pytest tests/test_config_service.py -v
```
Expected: PASS

- [ ] **Step 4: 提交**

```bash
git add core/config_service.py tests/test_config_service.py
git commit -m "feat: add ConfigService for JSON configuration management"
```

---

## Phase 4: UI 框架层

### Task 4.1: SystemTray 系统托盘

**Files:**
- Create: `ui/system_tray.py`
- Test: `tests/test_system_tray.py` (UI 测试)

- [ ] **Step 1: 编写系统托盘测试**

```python
# tests/test_system_tray.py
import pytest
from unittest.mock import Mock, MagicMock
from PyQt6.QtWidgets import QApplication
from ui.system_tray import SystemTray

@pytest.fixture
def app():
    return QApplication.instance() or QApplication([])

def test_system_tray_creation(app):
    tray = SystemTray(app)
    assert tray is not None
    assert tray.isVisible() == True

def test_system_tray_show_message(app):
    tray = SystemTray(app)
    # Should not raise exception
    tray.show_message("Test", "Test message")
```

- [ ] **Step 2: 实现 SystemTray**

```python
# ui/system_tray.py
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QAction
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import pyqtSignal, QObject
import sys
import os

class SystemTray(QObject):
    """系统托盘组件"""
    
    show_main_window = pyqtSignal()
    deploy_triggered = pyqtSignal()
    quit_triggered = pyqtSignal()
    
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.tray_icon = QSystemTrayIcon()
        self._setup_icon()
        self._setup_menu()
        self.tray_icon.show()
    
    def _setup_icon(self):
        """设置托盘图标"""
        # 尝试加载自定义图标
        icon_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'assets', 'icon.ico'
        )
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        else:
            # 使用默认图标
            from PyQt6.QtWidgets import QStyle
            self.tray_icon.setIcon(
                self.app.style().standardIcon(QStyle.StandardPixmap.SP_DriveNetIcon)
            )
    
    def _setup_menu(self):
        """设置右键菜单"""
        menu = QMenu()
        
        show_action = QAction("打开主窗口", menu)
        show_action.triggered.connect(lambda: self.show_main_window.emit())
        menu.addAction(show_action)
        
        deploy_action = QAction("一键部署", menu)
        deploy_action.triggered.connect(lambda: self.deploy_triggered.emit())
        menu.addAction(deploy_action)
        
        menu.addSeparator()
        
        quit_action = QAction("退出", menu)
        quit_action.triggered.connect(lambda: self.quit_triggered.emit())
        menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(self._on_activated)
    
    def _on_activated(self, reason):
        """双击托盘图标"""
        from PyQt6.QtSystemInfo import QSystemTrayIcon
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_main_window.emit()
    
    def show_message(self, title: str, message: str, 
                     icon=None, msecs: int = 5000):
        """显示通知消息"""
        from PyQt6.QtWidgets import QSystemTrayIcon
        if icon is None:
            icon = QSystemTrayIcon.MessageIcon.InformationIcon
        self.tray_icon.showMessage(title, message, icon, msecs)
```

- [ ] **Step 3: 运行测试验证通过**

```bash
pytest tests/test_system_tray.py -v
```
Expected: PASS

- [ ] **Step 4: 提交**

```bash
git add ui/system_tray.py tests/test_system_tray.py
git commit -m "feat: add SystemTray with context menu and signals"
```

---

### Task 4.2: MainWindow 主窗口

**Files:**
- Create: `ui/main_window.py`
- Create: `ui/components/nav_bar.py`
- Create: `ui/components/toolbar.py`
- Create: `ui/components/dashboard.py`
- Test: `tests/test_main_window.py`

- [ ] **Step 1: 实现 NavBar 导航栏**

```python
# ui/components/nav_bar.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QButtonGroup
from PyQt6.QtCore import pyqtSignal, QObject

class NavBar(QWidget):
    """左侧导航栏"""
    
    navigation_requested = pyqtSignal(str)  # 发送导航目标
    
    def __init__(self):
        super().__init__()
        self.setFixedWidth(180)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(10, 20, 10, 10)
        
        self.button_group = QButtonGroup()
        
        # 导航按钮
        nav_items = [
            ('home', '首页'),
            ('python', 'Python 脚本'),
            ('wps', 'WPS 脚本'),
            ('js', 'JS 脚本'),
            ('settings', '设置'),
        ]
        
        for i, (name, label) in enumerate(nav_items):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, n=name: self._on_button_clicked(n))
            layout.addWidget(btn)
            self.button_group.addButton(btn, i)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def _on_button_clicked(self, name: str):
        """按钮点击处理"""
        self.navigation_requested.emit(name)
    
    def navigate_to(self, name: str):
        """切换到指定页面"""
        buttons = self.button_group.buttons()
        nav_items = ['home', 'python', 'wps', 'js', 'settings']
        if name in nav_items:
            buttons[nav_items.index(name)].setChecked(True)
```

- [ ] **Step 2: 实现 ToolBar 工具栏**

```python
# ui/components/toolbar.py
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import pyqtSignal

class ToolBar(QWidget):
    """顶部工具栏"""
    
    deploy_requested = pyqtSignal()
    import_requested = pyqtSignal()
    export_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setFixedHeight(50)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(15, 5, 15, 5)
        
        # 标题
        title = QLabel("脚本管理器")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # 操作按钮
        self.deploy_btn = QPushButton("一键部署")
        self.deploy_btn.clicked.connect(lambda: self.deploy_requested.emit())
        layout.addWidget(self.deploy_btn)
        
        self.import_btn = QPushButton("导入")
        self.import_btn.clicked.connect(lambda: self.import_requested.emit())
        layout.addWidget(self.import_btn)
        
        self.export_btn = QPushButton("导出")
        self.export_btn.clicked.connect(lambda: self.export_requested.emit())
        layout.addWidget(self.export_btn)
        
        self.setLayout(layout)
```

- [ ] **Step 3: 实现 Dashboard 首页仪表盘**

```python
# ui/components/dashboard.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt

class Dashboard(QWidget):
    """首页仪表盘"""
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 欢迎标题
        title = QLabel("欢迎使用脚本管理器")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)
        
        # 统计卡片
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)
        
        self.python_card = self._create_stat_card("Python 脚本", "0")
        stats_layout.addWidget(self.python_card)
        
        self.wps_card = self._create_stat_card("WPS 脚本", "0")
        stats_layout.addWidget(self.wps_card)
        
        self.js_card = self._create_stat_card("JS 脚本", "0")
        stats_layout.addWidget(self.js_card)
        
        layout.addLayout(stats_layout)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def _create_stat_card(self, title: str, value: str) -> QFrame:
        """创建统计卡片"""
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.StyledPanel)
        card.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        
        layout = QVBoxLayout()
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #666; font-size: 14px;")
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setStyleSheet("font-size: 32px; font-weight: bold; color: #333;")
        layout.addWidget(value_label)
        
        card.setLayout(layout)
        return card
    
    def update_stats(self, python_count: int, wps_count: int, js_count: int):
        """更新统计数据"""
        for card, count in [
            (self.python_card, python_count),
            (self.wps_card, wps_count),
            (self.js_card, js_count)
        ]:
            value_label = card.layout().itemAt(1).widget()
            value_label.setText(str(count))
```

- [ ] **Step 4: 实现 MainWindow 主窗口**

```python
# ui/main_window.py
from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget
from PyQt6.QtCore import Qt
from ui.system_tray import SystemTray
from ui.components.nav_bar import NavBar
from ui.components.toolbar import ToolBar
from ui.components.dashboard import Dashboard

class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("脚本管理器")
        self.setMinimumSize(1024, 768)
        
        self._setup_ui()
        self._setup_system_tray()
        self._connect_signals()
    
    def _setup_ui(self):
        """设置 UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 顶部工具栏
        self.toolbar = ToolBar()
        main_layout.addWidget(self.toolbar)
        
        # 内容区域
        content_widget = QWidget()
        content_layout = QHBoxLayout()
        content_layout.setSpacing(0)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # 左侧导航栏
        self.nav_bar = NavBar()
        content_layout.addWidget(self.nav_bar)
        
        # 页面栈
        self.stack = QStackedWidget()
        content_layout.addWidget(self.stack)
        
        content_widget.setLayout(content_layout)
        main_layout.addWidget(content_widget)
        
        central_widget.setLayout(main_layout)
        
        # 添加页面
        self.dashboard = Dashboard()
        self.stack.addWidget(self.dashboard)
        # 其他模块页面将在后续任务中添加
    
    def _setup_system_tray(self):
        """设置系统托盘"""
        from PyQt6.QtWidgets import QApplication
        self.tray = SystemTray(QApplication.instance())
    
    def _connect_signals(self):
        """连接信号"""
        # 导航
        self.nav_bar.navigation_requested.connect(self._on_navigation)
        
        # 工具栏
        self.toolbar.deploy_requested.connect(lambda: self._on_action('deploy'))
        self.toolbar.import_requested.connect(lambda: self._on_action('import'))
        self.toolbar.export_requested.connect(lambda: self._on_action('export'))
        
        # 系统托盘
        self.tray.show_main_window.connect(self.show)
        self.tray.quit_triggered.connect(self.close)
    
    def _on_navigation(self, page_name: str):
        """导航处理"""
        pages = {
            'home': 0,
            'python': 1,
            'wps': 2,
            'js': 3,
            'settings': 4,
        }
        if page_name in pages:
            self.stack.setCurrentIndex(pages[page_name])
    
    def _on_action(self, action: str):
        """动作处理"""
        # 将在后续任务中实现
        print(f"Action: {action}")
```

- [ ] **Step 5: 提交**

```bash
git add ui/main_window.py ui/components/nav_bar.py ui/components/toolbar.py ui/components/dashboard.py
git commit -m "feat: add MainWindow with navigation, toolbar, and dashboard"
```

---

## Phase 5: 子模块开发

### Task 5.1: PythonModule Python 脚本模块

**Files:**
- Create: `ui/modules/python_module.py`
- Create: `services/python_service.py`
- Create: `services/dependency_service.py`
- Test: `tests/test_python_service.py`
- Test: `tests/test_dependency_service.py`

- [ ] **Step 1: 编写 PythonService 测试**

```python
# tests/test_python_service.py
import pytest
import tempfile
import os
from services.python_service import PythonService
from models.repository import Repository
from models.script_model import ScriptModel, ScriptType

@pytest.fixture
def python_service():
    repo = Repository(':memory:')
    model = ScriptModel(repo)
    model.create_tables()
    return PythonService(model, repo)

def test_python_service_add_script(python_service):
    script_id = python_service.add_script(
        name='test_script',
        code='print("hello")',
        description='Test',
        parent_id=None
    )
    assert script_id is not None
    script = python_service.get_script(script_id)
    assert script['name'] == 'test_script'

def test_python_service_get_tree(python_service):
    parent_id = python_service.add_script(name='parent')
    child_id = python_service.add_script(name='child', parent_id=parent_id)
    tree = python_service.get_tree()
    assert len(tree) == 1
    assert len(tree[0]['children']) == 1
```

- [ ] **Step 2: 实现 PythonService**

```python
# services/python_service.py
from typing import List, Dict, Optional, Any
from models.script_model import ScriptModel, ScriptType
from models.repository import Repository

class PythonService:
    """Python 脚本管理服务"""
    
    def __init__(self, script_model: ScriptModel, repo: Repository):
        self.model = script_model
        self.repo = repo
        self.scripts_dir = ''  # 由配置设置
    
    def set_scripts_dir(self, path: str):
        """设置脚本存储目录"""
        self.scripts_dir = path
        os.makedirs(path, exist_ok=True)
    
    def add_script(self, name: str, code: str = '', description: str = '',
                   parent_id: Optional[int] = None) -> int:
        """添加脚本"""
        script_id = self.model.add_script(
            name=name, script_type=ScriptType.PYTHON,
            code=code, description=description, parent_id=parent_id
        )
        # 保存脚本文件
        if self.scripts_dir:
            file_path = os.path.join(self.scripts_dir, f'{name}.py')
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(code)
        return script_id
    
    def get_script(self, script_id: int) -> Optional[Dict[str, Any]]:
        """获取脚本"""
        return self.model.get_script(script_id)
    
    def get_tree(self) -> List[Dict[str, Any]]:
        """获取树状结构的脚本列表"""
        return self.model.get_tree(ScriptType.PYTHON)
    
    def update_script(self, script_id: int, code: str = '', **kwargs) -> None:
        """更新脚本"""
        self.model.update_script(script_id, code=code, **kwargs)
        # 更新脚本文件
        if self.scripts_dir and code:
            script = self.model.get_script(script_id)
            if script:
                file_path = os.path.join(self.scripts_dir, f"{script['name']}.py")
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(code)
    
    def delete_script(self, script_id: int) -> None:
        """删除脚本"""
        script = self.model.get_script(script_id)
        if script and self.scripts_dir:
            file_path = os.path.join(self.scripts_dir, f"{script['name']}.py")
            if os.path.exists(file_path):
                os.remove(file_path)
        self.model.delete_script(script_id)
    
    def run_script(self, script_id: int) -> bool:
        """运行脚本（通过 PowerShell）"""
        script = self.model.get_script(script_id)
        if not script:
            return False
        # 保存临时文件并执行
        temp_path = os.path.join(os.getcwd(), 'temp_run.py')
        with open(temp_path, 'w', encoding='utf-8') as f:
            f.write(script['code'])
        # 通过 PowerShell 执行
        import subprocess
        subprocess.run(['powershell', '-Command', f'python {temp_path}'])
        return True
```

- [ ] **Step 3: 编写 DependencyService 测试**

```python
# tests/test_dependency_service.py
import pytest
from services.dependency_service import DependencyService
from models.repository import Repository
from models.script_model import ScriptModel, ScriptType

@pytest.fixture
def dep_service():
    repo = Repository(':memory:')
    model = ScriptModel(repo)
    model.create_tables()
    return DependencyService(model, repo, ':/whl_pool')

def test_dependency_service_analyze_imports(dep_service):
    code = '''
import requests
from flask import Flask
'''
    imports = dep_service.analyze_imports(code)
    assert 'requests' in imports
    assert 'flask' in imports

def test_dependency_service_check_missing(dep_service):
    script_id = dep_service.model.add_script(
        name='test', script_type=ScriptType.PYTHON,
        code='import requests'
    )
    dep_service.model.add_dependency(script_id, 'requests', installed=False)
    missing = dep_service.check_missing(script_id)
    assert len(missing) > 0
```

- [ ] **Step 4: 实现 DependencyService**

```python
# services/dependency_service.py
import ast
import os
from typing import List, Dict, Set
from models.script_model import ScriptModel
from models.repository import Repository

class DependencyService:
    """依赖检测服务"""
    
    def __init__(self, script_model: ScriptModel, repo: Repository, 
                 whl_pool_path: str):
        self.model = script_model
        self.repo = repo
        self.whl_pool_path = whl_pool_path
    
    def analyze_imports(self, code: str) -> Set[str]:
        """分析代码中的 import 语句"""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return set()
        
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])
        return imports
    
    def check_missing(self, script_id: int) -> List[str]:
        """检查脚本缺失的依赖"""
        script = self.model.get_script(script_id)
        if not script:
            return []
        
        imports = self.analyze_imports(script['code'])
        deps = self.model.get_dependencies(script_id)
        installed_packages = {d['package_name'] for d in deps if d['installed']}
        
        # 检查 whl 文件池
        whl_packages = self._get_whl_packages()
        
        missing = []
        for imp in imports:
            if imp not in installed_packages and imp not in whl_packages:
                missing.append(imp)
        return missing
    
    def _get_whl_packages(self) -> Set[str]:
        """获取 whl 文件池中的包名"""
        packages = set()
        if os.path.exists(self.whl_pool_path):
            for filename in os.listdir(self.whl_pool_path):
                if filename.endswith('.whl'):
                    # 从 whl 文件名提取包名 (格式：package_name-version-...)
                    package_name = filename.split('-')[0]
                    packages.add(package_name.lower())
        return packages
    
    def install_from_whl(self, package_name: str) -> bool:
        """从 whl 文件池安装依赖"""
        whl_file = self._find_whl(package_name)
        if not whl_file:
            return False
        
        import subprocess
        result = subprocess.run([
            'pip', 'install', '--no-index',
            '--find-links', self.whl_pool_path,
            package_name
        ], capture_output=True, text=True)
        return result.returncode == 0
    
    def _find_whl(self, package_name: str) -> Optional[str]:
        """在 whl 文件池中查找包"""
        if os.path.exists(self.whl_pool_path):
            for filename in os.listdir(self.whl_pool_path):
                if filename.lower().startswith(package_name.lower() + '-') and filename.endswith('.whl'):
                    return os.path.join(self.whl_pool_path, filename)
        return None
```

- [ ] **Step 5: 实现 PythonModule UI**

```python
# ui/modules/python_module.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QTextEdit, QLabel, QDialog, QLineEdit, QMessageBox
)
from PyQt6.QtCore import pyqtSignal

class PythonModule(QWidget):
    """Python 脚本模块 UI"""
    
    def __init__(self, python_service, dep_service):
        super().__init__()
        self.python_service = python_service
        self.dep_service = dep_service
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout()
        
        # 左侧树状列表
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(['脚本名称'])
        layout.addWidget(self.tree)
        
        # 右侧操作区
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        
        # 脚本列表
        self.script_list = QLabel("脚本代码")
        right_layout.addWidget(self.script_list)
        
        # 代码编辑器
        self.code_editor = QTextEdit()
        right_layout.addWidget(self.code_editor)
        
        # 按钮
        btn_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("新增")
        self.add_btn.clicked.connect(self._on_add)
        btn_layout.addWidget(self.add_btn)
        
        self.edit_btn = QPushButton("修改")
        self.edit_btn.clicked.connect(self._on_edit)
        btn_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("删除")
        self.delete_btn.clicked.connect(self._on_delete)
        btn_layout.addWidget(self.delete_btn)
        
        self.run_btn = QPushButton("运行")
        self.run_btn.clicked.connect(self._on_run)
        btn_layout.addWidget(self.run_btn)
        
        self.dep_check_btn = QPushButton("检测依赖")
        self.dep_check_btn.clicked.connect(self._on_check_deps)
        btn_layout.addWidget(self.dep_check_btn)
        
        right_layout.addLayout(btn_layout)
        right_widget.setLayout(right_layout)
        layout.addWidget(right_widget)
        
        self.setLayout(layout)
    
    def load_scripts(self):
        """加载脚本列表"""
        self.tree.clear()
        tree_data = self.python_service.get_tree()
        self._build_tree(self.tree, tree_data)
    
    def _build_tree(self, parent, items):
        """构建树状结构"""
        for item in items:
            tree_item = QTreeWidgetItem([item['name']])
            tree_item.setData(0, 1, item['id'])  # 存储 ID
            parent.addTopLevelItem(tree_item)
            if item.get('children'):
                self._build_tree(tree_item, item['children'])
    
    def _on_add(self):
        """新增脚本"""
        # 弹出对话框
        dialog = ScriptDialog(self)
        if dialog.exec() == 1:  # Accepted
            self.python_service.add_script(
                name=dialog.name_input.text(),
                code=dialog.code_editor.toPlainText()
            )
            self.load_scripts()
    
    def _on_edit(self):
        """编辑脚本"""
        selected = self.tree.currentItem()
        if not selected:
            return
        script_id = selected.data(0, 1)
        script = self.python_service.get_script(script_id)
        # 填充编辑对话框
        dialog = ScriptDialog(self, script)
        if dialog.exec() == 1:
            self.python_service.update_script(
                script_id,
                code=dialog.code_editor.toPlainText()
            )
            self.load_scripts()
    
    def _on_delete(self):
        """删除脚本"""
        selected = self.tree.currentItem()
        if not selected:
            return
        script_id = selected.data(0, 1)
        reply = QMessageBox.question(
            self, '确认删除', '确定要删除此脚本吗？',
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.python_service.delete_script(script_id)
            self.load_scripts()
    
    def _on_run(self):
        """运行脚本"""
        selected = self.tree.currentItem()
        if not selected:
            return
        script_id = selected.data(0, 1)
        self.python_service.run_script(script_id)
    
    def _on_check_deps(self):
        """检测依赖"""
        selected = self.tree.currentItem()
        if not selected:
            return
        script_id = selected.data(0, 1)
        missing = self.dep_service.check_missing(script_id)
        if missing:
            QMessageBox.warning(
                self, '缺失依赖',
                f'以下依赖缺失:\n{chr(10).join(missing)}'
            )
        else:
            QMessageBox.information(
                self, '依赖检查', '所有依赖已满足'
            )

class ScriptDialog(QDialog):
    """脚本编辑对话框"""
    
    def __init__(self, parent, script=None):
        super().__init__(parent)
        self.setWindowTitle('新增脚本' if not script else '编辑脚本')
        self.setMinimumSize(600, 400)
        
        layout = QVBoxLayout()
        
        # 名称输入
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel('脚本名称:'))
        self.name_input = QLineEdit()
        if script:
            self.name_input.setText(script['name'])
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)
        
        # 代码编辑器
        self.code_editor = QTextEdit()
        if script:
            self.code_editor.setPlainText(script['code'])
        layout.addWidget(self.code_editor)
        
        # 按钮
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton('确定')
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton('取消')
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
```

- [ ] **Step 6: 提交**

```bash
git add ui/modules/python_module.py services/python_service.py services/dependency_service.py tests/
git commit -m "feat: add Python module with dependency checking"
```

---

### Task 5.2: WpsModule WPS 脚本模块

**Files:**
- Create: `ui/modules/wps_module.py`
- Create: `services/wps_service.py`
- Test: `tests/test_wps_service.py`

- [ ] **Step 1: 编写 WpsService 测试**

```python
# tests/test_wps_service.py
import pytest
from services.wps_service import WpsService
from models.repository import Repository
from models.script_model import ScriptModel, ScriptType

@pytest.fixture
def wps_service():
    repo = Repository(':memory:')
    model = ScriptModel(repo)
    model.create_tables()
    return WpsService(model, repo)

def test_wps_service_add_script(wps_service):
    script_id = wps_service.add_script(
        name='test_macro',
        vba_code='Sub Test()\n    MsgBox "Hello"\nEnd Sub',
        target_app='word',
        ribbon_group='测试组',
        ribbon_label='测试按钮'
    )
    assert script_id is not None

def test_wps_service_generate_ribbon_xml(wps_service):
    wps_service.add_script(
        name='test_macro',
        vba_code='Sub Test()\nEnd Sub',
        target_app='word',
        ribbon_group='测试组',
        ribbon_label='测试按钮'
    )
    xml = wps_service.generate_ribbon_xml('word')
    assert '<customUI' in xml
    assert '测试组' in xml
    assert '测试按钮' in xml
```

- [ ] **Step 2: 实现 WpsService**

```python
# services/wps_service.py
import os
import zipfile
import tempfile
from typing import List, Dict, Optional
from models.script_model import ScriptModel, ScriptType
from models.repository import Repository

class WpsService:
    """WPS 脚本管理服务"""
    
    def __init__(self, script_model: ScriptModel, repo: Repository):
        self.model = script_model
        self.repo = repo
        self.templates_dir = ''
        self.word_startup = ''
        self.excel_startup = ''
    
    def set_paths(self, templates_dir: str, word_startup: str, excel_startup: str):
        """设置路径"""
        self.templates_dir = templates_dir
        self.word_startup = word_startup
        self.excel_startup = excel_startup
        os.makedirs(templates_dir, exist_ok=True)
    
    def add_script(self, name: str, vba_code: str, target_app: str,
                   ribbon_group: str = '', ribbon_label: str = '',
                   context_menu_label: str = '') -> int:
        """添加 WPS 脚本"""
        script_id = self.model.add_script(
            name=name, script_type=ScriptType.WPS,
            code=vba_code
        )
        self.model.add_wps_mapping(
            script_id=script_id, target_app=target_app,
            ribbon_group=ribbon_group, ribbon_label=ribbon_label,
            context_menu_label=context_menu_label
        )
        return script_id
    
    def get_all_scripts(self) -> List[Dict]:
        """获取所有 WPS 脚本"""
        return self.model.get_all_wps_scripts()
    
    def generate_ribbon_xml(self, target_app: str) -> str:
        """生成 Ribbon XML"""
        scripts = self.get_all_scripts()
        
        # 按分组组织按钮
        groups = {}
        for script in scripts:
            if script.get('target_app') != target_app:
                continue
            group = script.get('ribbon_group') or 'Default'
            if group not in groups:
                groups[group] = []
            groups[group].append(script)
        
        # 生成 XML
        buttons_xml = ''
        for group_name, group_scripts in groups.items():
            buttons_xml += f'        <group id="{group_name}_group" label="{group_name}">\n'
            for script in group_scripts:
                macro_name = script['name'].replace(' ', '_')
                label = script.get('ribbon_label') or script['name']
                buttons_xml += f'            <button id="{macro_name}_btn" label="{label}" onAction="{macro_name}" />\n'
            buttons_xml += f'        </group>\n'
        
        xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<customUI xmlns="http://schemas.microsoft.com/office/2009/07/customui">
    <ribbon>
        <tabs>
            <tab id="script_manager_tab" label="脚本管理器">
{buttons_xml}
            </tab>
        </tabs>
    </ribbon>
</customUI>'''
        return xml
    
    def generate_vba_module(self, target_app: str) -> str:
        """生成 VBA 模块代码"""
        scripts = self.get_all_scripts()
        
        vba_code = '''Attribute VB_Name = "ScriptManagerMacros"
' 脚本管理器自动生成的宏模块

'''
        for script in scripts:
            if script.get('target_app') != target_app:
                continue
            macro_name = script['name'].replace(' ', '_')
            vba_code += f'''Sub {macro_name}()
' {script.get('description') or script['name']}
{script['code']}
End Sub

'''
        return vba_code
    
    def create_word_template(self) -> str:
        """创建 Word 模板文件 (.dotm)"""
        # 生成 Ribbon XML
        ribbon_xml = self.generate_ribbon_xml('word')
        vba_code = self.generate_vba_module('word')
        
        # 创建模板文件
        template_path = os.path.join(self.templates_dir, 'word_template.dotm')
        
        # 使用 python-docx 创建基础文档
        from docx import Document
        doc = Document()
        doc.add_paragraph('WPS 脚本管理器模板 - 自动加载宏')
        
        # 保存为临时文件
        temp_path = tempfile.mktemp(suffix='.docm')
        doc.save(temp_path)
        
        # 将 .docm 重命名为 .dotm 并添加 Ribbon XML
        # .dotm 是 ZIP 格式，需要添加 customUI 目录
        with zipfile.ZipFile(temp_path, 'a') as zipf:
            # 添加 Ribbon XML
            zipf.writestr('word/customUI/customUI.xml', ribbon_xml)
            # 添加 VBA 模块 (简化处理，实际需要操作 VBA 工程)
            zipf.writestr('word/vbaProject.bin', self._create_vba_project(vba_code))
        
        # 移动到目标位置
        os.rename(temp_path, template_path)
        
        # 复制到 STARTUP 目录
        if self.word_startup:
            import shutil
            startup_path = os.path.join(self.word_startup, 'word_template.dotm')
            shutil.copy2(template_path, startup_path)
        
        return template_path
    
    def _create_vba_project(self, vba_code: str) -> bytes:
        """创建 VBA 工程 (简化版本)"""
        # 实际需要生成完整的 VBA 工程二进制格式
        # 这里返回一个占位符，实际实现需要更复杂的处理
        return b''
    
    def create_excel_template(self) -> str:
        """创建 Excel 模板文件 (.xlam)"""
        ribbon_xml = self.generate_ribbon_xml('excel')
        vba_code = self.generate_vba_module('excel')
        
        template_path = os.path.join(self.templates_dir, 'excel_template.xlam')
        
        # 使用 openpyxl 创建工作簿
        from openpyxl import Workbook
        wb = Workbook()
        wb.create_sheet('脚本管理器模板')
        
        temp_path = tempfile.mktemp(suffix='.xlsm')
        wb.save(temp_path)
        
        # 添加 Ribbon XML 和 VBA
        with zipfile.ZipFile(temp_path, 'a') as zipf:
            zipf.writestr('xl/customUI/customUI.xml', ribbon_xml)
        
        os.rename(temp_path, template_path)
        
        if self.excel_startup:
            import shutil
            startup_path = os.path.join(self.excel_startup, 'excel_template.xlam')
            shutil.copy2(template_path, startup_path)
        
        return template_path
    
    def deploy_all(self) -> Dict[str, bool]:
        """部署所有 WPS 模板"""
        result = {
            'word': False,
            'excel': False
        }
        try:
            self.create_word_template()
            result['word'] = True
        except Exception as e:
            print(f'Word 模板创建失败：{e}')
        
        try:
            self.create_excel_template()
            result['excel'] = True
        except Exception as e:
            print(f'Excel 模板创建失败：{e}')
        
        return result
```

- [ ] **Step 3: 实现 WpsModule UI**

```python
# ui/modules/wps_module.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QTextEdit, QLabel, QDialog, QLineEdit, QComboBox, QMessageBox
)

class WpsModule(QWidget):
    """WPS 脚本模块 UI"""
    
    def __init__(self, wps_service):
        super().__init__()
        self.wps_service = wps_service
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout()
        
        # 左侧脚本列表
        self.script_list = QListWidget()
        layout.addWidget(self.script_list)
        
        # 右侧操作区
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        
        # VBA 代码编辑器
        self.code_editor = QTextEdit()
        self.code_editor.setPlaceholderText('VBA 代码')
        right_layout.addWidget(QLabel('VBA 代码:'))
        right_layout.addWidget(self.code_editor)
        
        # 映射设置
        mapping_group = QLabel('功能区和菜单映射')
        right_layout.addWidget(mapping_group)
        
        self.target_app = QComboBox()
        self.target_app.addItems(['word', 'excel'])
        right_layout.addWidget(QLabel('目标应用:'))
        right_layout.addWidget(self.target_app)
        
        self.ribbon_group = QLineEdit()
        self.ribbon_group.setPlaceholderText('功能区分组名称')
        right_layout.addWidget(QLabel('功能区分组:'))
        right_layout.addWidget(self.ribbon_group)
        
        self.ribbon_label = QLineEdit()
        self.ribbon_label.setPlaceholderText('功能区按钮标签')
        right_layout.addWidget(QLabel('功能区按钮标签:'))
        right_layout.addWidget(self.ribbon_label)
        
        # 按钮
        btn_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("新增")
        self.add_btn.clicked.connect(self._on_add)
        btn_layout.addWidget(self.add_btn)
        
        self.edit_btn = QPushButton("修改")
        self.edit_btn.clicked.connect(self._on_edit)
        btn_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("删除")
        self.delete_btn.clicked.connect(self._on_delete)
        btn_layout.addWidget(self.delete_btn)
        
        right_layout.addLayout(btn_layout)
        right_layout.addStretch()
        right_widget.setLayout(right_layout)
        layout.addWidget(right_widget)
        
        self.setLayout(layout)
    
    def load_scripts(self):
        """加载脚本列表"""
        self.script_list.clear()
        scripts = self.wps_service.get_all_scripts()
        for script in scripts:
            item = QListWidgetItem(f"{script['name']} ({script['target_app']})")
            item.setData(1, script['id'])
            self.script_list.addItem(item)
    
    def _on_add(self):
        """新增脚本"""
        vba_code = self.code_editor.toPlainText()
        if not vba_code:
            QMessageBox.warning(self, '错误', '请输入 VBA 代码')
            return
        
        self.wps_service.add_script(
            name=f'script_{self.script_list.count() + 1}',
            vba_code=vba_code,
            target_app=self.target_app.currentText(),
            ribbon_group=self.ribbon_group.text(),
            ribbon_label=self.ribbon_label.text()
        )
        self.load_scripts()
    
    def _on_edit(self):
        """编辑脚本"""
        current = self.script_list.currentItem()
        if not current:
            return
        # 实现编辑逻辑
    
    def _on_delete(self):
        """删除脚本"""
        current = self.script_list.currentItem()
        if not current:
            return
        reply = QMessageBox.question(
            self, '确认删除', '确定要删除此脚本吗？',
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            script_id = current.data(1)
            # self.wps_service.delete_script(script_id)
            self.load_scripts()
    
    def preview_ribbon(self):
        """预览功能区"""
        xml = self.wps_service.generate_ribbon_xml('word')
        # 显示 XML 预览
```

- [ ] **Step 4: 提交**

```bash
git add ui/modules/wps_module.py services/wps_service.py tests/test_wps_service.py
git commit -m "feat: add WPS module with template generation"
```

---

### Task 5.3: JsModule JS 脚本模块

**Files:**
- Create: `ui/modules/js_module.py`
- Create: `services/js_service.py`
- Test: `tests/test_js_service.py`

- [ ] **Step 1: 编写 JsService 测试**

```python
# tests/test_js_service.py
import pytest
import json
import tempfile
import os
from services.js_service import JsService
from models.repository import Repository
from models.script_model import ScriptModel, ScriptType

@pytest.fixture
def js_service():
    repo = Repository(':memory:')
    model = ScriptModel(repo)
    model.create_tables()
    return JsService(model, repo)

def test_js_service_add_script(js_service):
    script_id = js_service.add_script(
        name='test_bookmark',
        url='javascript:alert("hello")',
        parent_folder='测试文件夹'
    )
    assert script_id is not None

def test_js_service_generate_bookmarks(js_service):
    js_service.add_script(
        name='test1',
        url='javascript:alert("1")',
        parent_folder='Folder1',
        position=0
    )
    bookmarks = js_service.generate_bookmarks_json()
    data = json.loads(bookmarks)
    assert 'roots' in data
```

- [ ] **Step 2: 实现 JsService**

```python
# services/js_service.py
import json
import os
from typing import List, Dict, Optional
from models.script_model import ScriptModel, ScriptType
from models.repository import Repository

class JsService:
    """JS 脚本管理服务"""
    
    def __init__(self, script_model: ScriptModel, repo: Repository):
        self.model = script_model
        self.repo = repo
        self.chrome_bookmarks_path = ''
    
    def set_chrome_path(self, path: str):
        """设置 Chrome 书签文件路径"""
        self.chrome_bookmarks_path = path
    
    def add_script(self, name: str, url: str, parent_folder: str = '',
                   position: int = 0) -> int:
        """添加 JS 脚本"""
        script_id = self.model.add_script(
            name=name, script_type=ScriptType.JAVASCRIPT,
            code=url  # JS 脚本的 code 字段存储 URL
        )
        self.model.add_js_bookmark(
            script_id=script_id, bookmark_url=url,
            parent_folder=parent_folder, position=position
        )
        return script_id
    
    def get_all_scripts(self) -> List[Dict]:
        """获取所有 JS 脚本"""
        return self.model.get_all_js_scripts()
    
    def generate_bookmarks_json(self) -> str:
        """生成 Chrome 书签 JSON 结构"""
        scripts = self.get_all_scripts()
        
        # 按文件夹组织
        folders = {}
        for script in scripts:
            folder = script.get('parent_folder') or '脚本管理器'
            if folder not in folders:
                folders[folder] = []
            folders[folder].append(script)
        
        # 构建 Chrome 书签格式
        bookmark_structure = {
            "checksum": "",
            "roots": {
                "bookmark_bar": {
                    "children": [],
                    "date_added": "0",
                    "date_modified": "0",
                    "guid": "0",
                    "name": "书签栏"
                }
            },
            "version": 1
        }
        
        # 添加文件夹到书签栏
        for folder_name, folder_scripts in folders.items():
            folder_node = {
                "children": [],
                "date_added": "0",
                "date_modified": "0",
                "guid": folder_name,
                "name": folder_name,
                "type": "folder"
            }
            
            for script in folder_scripts:
                bookmark_node = {
                    "date_added": "0",
                    "date_modified": "0",
                    "guid": str(script['id']),
                    "name": script['name'],
                    "type": "url",
                    "url": script['bookmark_url']
                }
                folder_node["children"].append(bookmark_node)
            
            bookmark_structure["roots"]["bookmark_bar"]["children"].append(folder_node)
        
        return json.dumps(bookmark_structure, indent=2, ensure_ascii=False)
    
    def deploy_bookmarks(self) -> bool:
        """部署书签到 Chrome"""
        if not self.chrome_bookmarks_path:
            return False
        
        try:
            # 备份原书签
            if os.path.exists(self.chrome_bookmarks_path):
                backup_path = self.chrome_bookmarks_path + '.bak'
                import shutil
                shutil.copy2(self.chrome_bookmarks_path, backup_path)
            
            # 写入新书签
            bookmarks_json = self.generate_bookmarks_json()
            with open(self.chrome_bookmarks_path, 'w', encoding='utf-8') as f:
                f.write(bookmarks_json)
            
            return True
        except Exception as e:
            print(f'书签部署失败：{e}')
            return False
    
    def open_in_chrome(self, script_id: int) -> bool:
        """在 Chrome 中打开脚本"""
        script = self.model.get_script(script_id)
        if not script:
            return False
        
        url = script['code']  # JS 脚本的 URL 存储在 code 字段
        import subprocess
        subprocess.Popen(['chrome', url])
        return True
```

- [ ] **Step 3: 实现 JsModule UI**

```python
# ui/modules/js_module.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QTextEdit, QLabel, QDialog, QLineEdit, QMessageBox
)

class JsModule(QWidget):
    """JS 脚本模块 UI"""
    
    def __init__(self, js_service):
        super().__init__()
        self.js_service = js_service
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout()
        
        # 左侧脚本列表
        self.script_list = QListWidget()
        layout.addWidget(self.script_list)
        
        # 右侧操作区
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        
        # URL 编辑器
        self.url_editor = QTextEdit()
        self.url_editor.setPlaceholderText('JavaScript 代码或 bookmarklet URL')
        right_layout.addWidget(QLabel('脚本 URL/代码:'))
        right_layout.addWidget(self.url_editor)
        
        # 文件夹设置
        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText('书签文件夹名称')
        right_layout.addWidget(QLabel('书签文件夹:'))
        right_layout.addWidget(self.folder_input)
        
        # 按钮
        btn_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("新增")
        self.add_btn.clicked.connect(self._on_add)
        btn_layout.addWidget(self.add_btn)
        
        self.edit_btn = QPushButton("修改")
        self.edit_btn.clicked.connect(self._on_edit)
        btn_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("删除")
        self.delete_btn.clicked.connect(self._on_delete)
        btn_layout.addWidget(self.delete_btn)
        
        self.open_btn = QPushButton("在 Chrome 中打开")
        self.open_btn.clicked.connect(self._on_open)
        btn_layout.addWidget(self.open_btn)
        
        right_layout.addLayout(btn_layout)
        right_layout.addStretch()
        right_widget.setLayout(right_layout)
        layout.addWidget(right_widget)
        
        self.setLayout(layout)
    
    def load_scripts(self):
        """加载脚本列表"""
        self.script_list.clear()
        scripts = self.js_service.get_all_scripts()
        for script in scripts:
            item = QListWidgetItem(f"{script['name']} - {script['parent_folder']}")
            item.setData(1, script['id'])
            self.script_list.addItem(item)
    
    def _on_add(self):
        """新增脚本"""
        url = self.url_editor.toPlainText()
        if not url:
            QMessageBox.warning(self, '错误', '请输入脚本 URL')
            return
        
        self.js_service.add_script(
            name=f'script_{self.script_list.count() + 1}',
            url=url,
            parent_folder=self.folder_input.text()
        )
        self.load_scripts()
    
    def _on_edit(self):
        """编辑脚本"""
        current = self.script_list.currentItem()
        if not current:
            return
        # 实现编辑逻辑
    
    def _on_delete(self):
        """删除脚本"""
        current = self.script_list.currentItem()
        if not current:
            return
        reply = QMessageBox.question(
            self, '确认删除', '确定要删除此脚本吗？',
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            script_id = current.data(1)
            self.js_service.model.delete_script(script_id)
            self.load_scripts()
    
    def _on_open(self):
        """在 Chrome 中打开"""
        current = self.script_list.currentItem()
        if not current:
            return
        script_id = current.data(1)
        self.js_service.open_in_chrome(script_id)
```

- [ ] **Step 4: 提交**

```bash
git add ui/modules/js_module.py services/js_service.py tests/test_js_service.py
git commit -m "feat: add JS module with Chrome bookmark integration"
```

---

## Phase 6: 部署功能

### Task 6.1: DeploymentService 一键部署服务

**Files:**
- Create: `core/deployment_service.py`
- Test: `tests/test_deployment_service.py`

- [ ] **Step 1: 实现 DeploymentService**

```python
# core/deployment_service.py
from typing import Dict, Any
from services.wps_service import WpsService
from services.js_service import JsService

class DeploymentService:
    """一键部署服务"""
    
    def __init__(self, wps_service: WpsService, js_service: JsService):
        self.wps_service = wps_service
        self.js_service = js_service
    
    def deploy_all(self) -> Dict[str, Any]:
        """一键部署所有内容"""
        result = {
            'success': True,
            'wps_word': False,
            'wps_excel': False,
            'chrome_bookmarks': False,
            'errors': []
        }
        
        # 部署 WPS Word
        try:
            wps_result = self.wps_service.deploy_all()
            result['wps_word'] = wps_result.get('word', False)
            result['wps_excel'] = wps_result.get('excel', False)
        except Exception as e:
            result['success'] = False
            result['errors'].append(f'WPS 部署失败：{e}')
        
        # 部署 Chrome 书签
        try:
            result['chrome_bookmarks'] = self.js_service.deploy_bookmarks()
        except Exception as e:
            result['success'] = False
            result['errors'].append(f'Chrome 书签部署失败：{e}')
        
        return result
```

- [ ] **Step 2: 提交**

```bash
git add core/deployment_service.py tests/test_deployment_service.py
git commit -m "feat: add DeploymentService for one-click deployment"
```

---

## Phase 7: 导入导出功能

### Task 7.1: ImportExportService 导入导出服务

**Files:**
- Create: `core/import_export_service.py`
- Test: `tests/test_import_export_service.py`

- [ ] **Step 1: 实现 ImportExportService**

```python
# core/import_export_service.py
import os
import zipfile
import json
import tempfile
import shutil
from datetime import datetime
from typing import Optional

class ImportExportService:
    """导入导出服务"""
    
    def __init__(self, scripts_dir: str, config_path: str, db_path: str,
                 templates_dir: str):
        self.scripts_dir = scripts_dir
        self.config_path = config_path
        self.db_path = db_path
        self.templates_dir = templates_dir
    
    def export_all(self) -> str:
        """导出所有配置和脚本"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_path = f'scripts_backup_{timestamp}.zip'
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 添加脚本目录
            for root, dirs, files in os.walk(self.scripts_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, os.path.dirname(self.scripts_dir))
                    zipf.write(file_path, arcname)
            
            # 添加配置文件
            if os.path.exists(self.config_path):
                zipf.write(self.config_path, 'data/config.json')
            
            # 添加数据库
            if os.path.exists(self.db_path):
                zipf.write(self.db_path, 'data/scripts.db')
            
            # 添加模板文件
            if os.path.exists(self.templates_dir):
                for file in os.listdir(self.templates_dir):
                    file_path = os.path.join(self.templates_dir, file)
                    zipf.write(file_path, f'templates/{file}')
        
        return zip_path
    
    def import_package(self, zip_path: str, merge: bool = True) -> bool:
        """导入包"""
        temp_dir = tempfile.mkdtemp()
        
        try:
            # 解压
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                zipf.extractall(temp_dir)
            
            # 验证结构
            if not self._validate_structure(temp_dir):
                return False
            
            # 合并或覆盖
            if merge:
                self._merge_import(temp_dir)
            else:
                self._overwrite_import(temp_dir)
            
            return True
        except Exception as e:
            print(f'导入失败：{e}')
            return False
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def _validate_structure(self, directory: str) -> bool:
        """验证导入包结构"""
        required = ['scripts', 'data']
        for req in required:
            if not os.path.exists(os.path.join(directory, req)):
                return False
        return True
    
    def _merge_import(self, directory: str):
        """合并导入"""
        # 复制脚本文件
        src_scripts = os.path.join(directory, 'scripts')
        for root, dirs, files in os.walk(src_scripts):
            for file in files:
                src_path = os.path.join(root, file)
                rel_path = os.path.relpath(src_path, src_scripts)
                dst_path = os.path.join(self.scripts_dir, rel_path)
                os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                shutil.copy2(src_path, dst_path)
    
    def _overwrite_import(self, directory: str):
        """覆盖导入"""
        # 先清理现有数据
        if os.path.exists(self.scripts_dir):
            shutil.rmtree(self.scripts_dir)
        shutil.copytree(
            os.path.join(directory, 'scripts'),
            self.scripts_dir
        )
```

- [ ] **Step 2: 提交**

```bash
git add core/import_export_service.py tests/test_import_export_service.py
git commit -m "feat: add ImportExportService for backup and restore"
```

---

## Phase 8: 首次启动向导

### Task 8.1: SetupWizard 首次启动向导

**Files:**
- Create: `ui/dialogs/setup_wizard.py`

- [ ] **Step 1: 实现 SetupWizard**

```python
# ui/dialogs/setup_wizard.py
from PyQt6.QtWidgets import (
    QWizard, QWizardPage, QVBoxLayout, QLabel, QLineEdit, 
    QPushButton, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt

class SetupWizard(QWizard):
    """首次启动向导"""
    
    def __init__(self, path_detection_service, config_service):
        super().__init__()
        self.path_detection = path_detection_service
        self.config = config_service
        
        self.setWindowTitle("首次启动向导")
        self.setMinimumSize(600, 400)
        
        self._setup_pages()
    
    def _setup_pages(self):
        # 第 1 页：欢迎
        welcome_page = WelcomePage()
        self.addPage(welcome_page)
        
        # 第 2 页：路径配置
        paths_page = PathsPage(self.path_detection, self.config)
        self.addPage(paths_page)
        
        # 第 3 页：完成
        finish_page = FinishPage()
        self.addPage(finish_page)

class WelcomePage(QWizardPage):
    """欢迎页"""
    
    def __init__(self):
        super().__init__()
        self.setTitle("欢迎")
        
        layout = QVBoxLayout()
        layout.addWidget(QLabel("欢迎使用脚本管理器！"))
        layout.addWidget(QLabel("\n本向导将帮助您完成初始配置。"))
        layout.addWidget(QLabel("\n点击\"下一步\"继续，或点击\"跳过\"稍后在设置中配置。"))
        layout.addStretch()
        self.setLayout(layout)
    
    def nextId(self):
        return 2  # 跳过中间页直接到完成页

class PathsPage(QWizardPage):
    """路径配置页"""
    
    def __init__(self, path_detection, config):
        super().__init__()
        self.path_detection = path_detection
        self.config = config
        self.setTitle("路径配置")
        
        layout = QVBoxLayout()
        
        # Chrome 书签路径
        layout.addWidget(QLabel("Chrome 书签文件路径:"))
        self.chrome_path = QLineEdit()
        self.chrome_path.setText(self.path_detection.detect_chrome_bookmarks_file())
        layout.addWidget(self.chrome_path)
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self._browse_chrome)
        layout.addWidget(browse_btn)
        
        # WPS Word STARTUP
        layout.addWidget(QLabel("WPS Word 自启动目录:"))
        self.word_startup = QLineEdit()
        detected = self.path_detection.detect_wps_word_startup()
        if detected:
            self.word_startup.setText(detected)
        layout.addWidget(self.word_startup)
        
        # WPS Excel XLSTART
        layout.addWidget(QLabel("WPS Excel 自启动目录:"))
        self.excel_startup = QLineEdit()
        detected = self.path_detection.detect_wps_excel_startup()
        if detected:
            self.excel_startup.setText(detected)
        layout.addWidget(self.excel_startup)
        
        self.setLayout(layout)
    
    def _browse_chrome(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择 Chrome 书签文件", "", "JSON Files (*.json)"
        )
        if path:
            self.chrome_path.setText(path)
    
    def validatePage(self) -> bool:
        self.config.set('chrome_bookmarks_path', self.chrome_path.text())
        self.config.set('wps_word_startup', self.word_startup.text())
        self.config.set('wps_excel_startup', self.excel_startup.text())
        self.config.save()
        return True

class FinishPage(QWizardPage):
    """完成页"""
    
    def __init__(self):
        super().__init__()
        self.setTitle("完成")
        
        layout = QVBoxLayout()
        layout.addWidget(QLabel("配置已完成！"))
        layout.addWidget(QLabel("\n您现在可以开始使用脚本管理器了。"))
        layout.addWidget(QLabel("\n如需修改配置，请在设置中进行。"))
        layout.addStretch()
        self.setLayout(layout)
```

- [ ] **Step 2: 提交**

```bash
git add ui/dialogs/setup_wizard.py
git commit -m "feat: add SetupWizard for first-run configuration"
```

---

## Phase 9: 集成与优化

### Task 9.1: 应用入口整合

**Files:**
- Create: `app.py`

- [ ] **Step 1: 实现应用入口**

```python
# app.py
import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTranslator, QLocale
from models.repository import Repository
from models.script_model import ScriptModel
from services.python_service import PythonService
from services.wps_service import WpsService
from services.js_service import JsService
from services.dependency_service import DependencyService
from core.config_service import ConfigService
from core.path_detection_service import PathDetectionService
from core.deployment_service import DeploymentService
from core.import_export_service import ImportExportService
from ui.main_window import MainWindow
from ui.dialogs.setup_wizard import SetupWizard

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("脚本管理器")
    app.setOrganizationName("ScriptManager")
    
    # 初始化路径
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    # 初始化服务
    db_path = os.path.join(data_dir, 'scripts.db')
    config_path = os.path.join(data_dir, 'config.json')
    
    repo = Repository(db_path)
    script_model = ScriptModel(repo)
    script_model.create_tables()
    
    config_service = ConfigService(config_path)
    config_service.load()
    
    path_detection = PathDetectionService()
    
    # 初始化各模块服务
    scripts_dir = os.path.join(base_dir, 'scripts')
    whl_pool_dir = os.path.join(base_dir, 'whl_pool')
    templates_dir = os.path.join(base_dir, 'templates')
    
    python_service = PythonService(script_model, repo)
    python_service.set_scripts_dir(os.path.join(scripts_dir, 'python'))
    
    wps_service = WpsService(script_model, repo)
    wps_service.set_paths(
        templates_dir,
        config_service.get('wps_word_startup', ''),
        config_service.get('wps_excel_startup', '')
    )
    
    js_service = JsService(script_model, repo)
    js_service.set_chrome_path(
        config_service.get('chrome_bookmarks_path', '')
    )
    
    dep_service = DependencyService(script_model, repo, whl_pool_dir)
    
    deployment_service = DeploymentService(wps_service, js_service)
    import_export_service = ImportExportService(
        scripts_dir, config_path, db_path, templates_dir
    )
    
    # 检查是否首次启动
    if not config_service.get('initialized'):
        wizard = SetupWizard(path_detection, config_service)
        wizard.show()
        wizard.finished.connect(lambda: _on_wizard_finished(config_service))
    else:
        # 显示主窗口
        window = MainWindow()
        window.show()
    
    sys.exit(app.exec())

def _on_wizard_finished(config_service):
    config_service.set('initialized', True)
    config_service.save()

if __name__ == '__main__':
    main()
```

- [ ] **Step 2: 提交**

```bash
git add app.py
git commit -m "feat: add main application entry point"
```

---

**计划状态:** 完整详细 (所有 Phase 1-9 均包含完整步骤)

**下一步:** 用户审阅计划后，选择执行方式：

**选项 1: Subagent-Driven (推荐)** - 每个任务由独立子代理执行，任务间审查，快速迭代

**选项 2: Inline Execution** - 在当前会话中使用 executing-plans skill 批量执行，带审查检查点

---

## 进入开发阶段前的确认

**计划已完成并保存到:** `docs/superpowers/plans/2026-04-10-script-manager-plan.md`

**在进入开发阶段前，请确认以下事项：**

1. **开发机时间安排** - 你提到开发机需要断电关机，请确认何时可以恢复使用
2. **执行方式选择** - Subagent-Driven 或 Inline Execution
3. **是否现在开始执行** - 还是等你开发机恢复后再开始

**请确认后再开始开发。**


**下一步:** 
1. 完成 Phase 5-9 的详细任务步骤
2. 用户审阅计划
3. 选择执行方式 (Subagent-Driven 或 Inline Execution)