# 错误日志与经验教训

## 2026-04-13: 跨机器部署时配置文件路径导致 PermissionError

### 问题描述
内网环境运行 app.py 时报错：
```
PermissionError: [WinError 5] 拒绝访问。：'C:\\Users\\L'
```

### 根本原因
外网机器运行后生成的 `config.json` 保存了绝对路径（如 `C:\Users\L\AppData\Roaming\Kingsoft\WPS Office\startup\wps`），复制到内网机器后，程序尝试访问这些不存在的路径导致权限错误。

### 修复方式

**1. 添加 ConfigService.get_path() 方法**

在 `core/config_service.py` 中：
```python
def get_path(self, key: str, default: str = "") -> str:
    """获取路径配置值，验证路径是否存在。
    
    Returns:
        如果路径存在则返回路径值，否则返回默认值。
    """
    value = self.get(key, default)
    if value and isinstance(value, str) and os.path.exists(value):
        return value
    return default
```

**2. 更新 MainWindow 加载路径逻辑**

在 `ui/main_window.py` 中：
```python
def _load_paths_from_config(self):
    # 使用 get_path() 验证路径存在
    scripts_dir = self.config_service.get_path("paths.scripts_dir", "")
    whl_pool_dir = self.config_service.get_path("paths.whl_pool_dir", "")
    templates_dir = self.config_service.get_path("paths.templates_dir", "")
    
    # 只在路径存在时使用配置值
    if scripts_dir and os.path.exists(scripts_dir):
        self.scripts_dir = scripts_dir
```

**3. 修复 SettingsDialog.save_config()**

```python
def save_config(self, config_service):
    config_service.set("paths.chrome_bookmarks", self.chrome_path_input.text())
    # ... other settings ...
    config_service.save()  # 添加保存调用
```

### 修复提交
- `d8901c5` - fix: path validation for cross-machine deployment

### 预防指南
1. **配置文件不应包含绝对路径**：使用相对路径或环境变量
2. **跨机器部署前重置配置**：删除 `config.json` 或提供配置导出/导入功能
3. **路径验证**：加载配置时验证路径是否存在，无效路径使用默认值
4. **环境检测**：使用 `PathDetectionService` 动态检测当前机器的路径

### 内网部署步骤

1. 在外网机器下载离线包：
   ```bash
   pip download PyQt6 PyQt6-sip PyQt6-Qt6 -d D:\offline_packages
   ```

2. 复制离线包到内网机器

3. 在内网安装：
   ```bash
   pip install --no-index --find-links=D:\offline_packages PyQt6
   ```

4. 删除外网配置文件（如果有）：
   ```bash
   del D:\ScriptNexus\data\config.json
   ```

5. 运行应用：
   ```bash
   cd D:\ScriptNexus
   python app.py
   ```

---

## 2026-04-13: WHL 下载重复弹窗和 pip 错误处理、WPS 模块 QMenu 导入错误残留

### 问题描述
1. 下载 WHL 时输入无效包名（如 '123'）会弹出两次相同的警告对话框
2. 输入不存在的包名（如 'hjh'）时显示原始 pip 错误信息，不够友好
3. WPS 模块 `_update_add_menu()` 方法中仍有 `from PyQt6.QtGui import QMenu` 错误导入

### 根本原因
1. WHL 下载功能移除了版本兼容性弹窗，但在 dialog 验证失败后未关闭对话框，用户可能再次点击
2. pip download 错误信息直接显示给用户，未解析和转换为用户友好的提示
3. `_update_add_menu()` 方法中的 QMenu 导入在之前的修复中被遗漏

### 修复方式

**1. 移除冗余弹窗**

在 `ui/modules/python_module.py` 中：
```python
def _on_download_whl(self):
    dialog = WheelDownloadDialog(self)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        # 验证在 dialog 内部完成，这里直接使用结果
        # 不再显示版本兼容性弹窗
        package_name = dialog.get_package_name()
        download_path = dialog.get_download_path()
        # 执行下载...
```

**2. pip 错误信息友好化**

```python
if result.returncode != 0:
    error_msg = result.stderr.strip()
    if "Could not find a version that satisfies the requirement" in error_msg:
        friendly_msg = f"找不到包 '{package_name}'\n\n" \
                       f"可能的原因：\n" \
                       f"1. 包名拼写错误\n" \
                       f"2. 该包在 PyPI 上不存在\n" \
                       f"3. 该包与当前 Python 版本不兼容"
    elif "No matching distribution found" in error_msg:
        friendly_msg = f"未找到匹配的包版本\n\n" \
                       f"请检查：\n" \
                       f"1. 包名是否正确\n" \
                       f"2. 当前 Python 版本是否支持该包"
```

**3. 修复 QMenu 导入**

在 `ui/modules/wps_module.py` 中：
```python
def _update_add_menu(self):
    """更新添加按钮的菜单"""
    # 注意：QMenu 已在按钮创建时导入，无需重复导入
    # 删除：from PyQt6.QtGui import QMenu
```

### 修复提交
- `5425a5e` - fix: WHL download error handling and QMenu import

### 预防指南
1. **对话框验证**：验证失败时显示警告后应保持对话框打开，让用户修正输入，而不是关闭后重新打开
2. **错误信息本地化**：技术错误信息应转换为用户友好的提示，包含可能的原因和解决方案
3. **批量修复**：修复导入错误时应全局搜索所有引用，避免遗漏
4. **代码审查**：多处使用同一类时，确保导入位置统一且正确

---

## 2026-04-13: QMenu 导入错误导致闪退、Dashboard 初始不刷新、WHL 下载缺少验证

### 问题描述
1. 点击 WPS 脚本按钮时应用闪退，报错 `ImportError: cannot import name 'QMenu' from 'PyQt6.QtGui'`
2. 登录后首页 Dashboard 显示脚本数量为 000，需要点击其他页面再返回才能正常显示
3. WHL 下载功能缺少包名验证，输入 '123' 会下载无效的 `123-0.0.1-py3-none-any.whl` 文件，且未显示当前 Python 版本

### 根本原因
1. PyQt6 中 `QMenu` 位于 `QtWidgets` 模块，而非 `QtGui` 模块
2. `set_services()` 方法加载配置后未调用 `_refresh_dashboard()` 刷新统计
3. WHL 下载对话框未实现包名验证逻辑，未获取并显示当前 Python 版本

### 修复方式

**1. QMenu 导入修复**

在 `ui/modules/wps_module.py` 中：
```python
# 错误
from PyQt6.QtGui import QMenu

# 正确
from PyQt6.QtWidgets import QMenu
```

**2. Dashboard 初始刷新**

在 `ui/main_window.py` 中：
```python
def set_services(self, path_detection_service, config_service, deployment_service=None):
    # ... existing code ...
    
    # Load paths from config if available
    self._load_paths_from_config()
    
    # Refresh dashboard stats on initial load
    self._refresh_dashboard()
```

**3. WHL 下载改进**

在 `ui/modules/python_module.py` 中：
```python
class WheelDownloadDialog(QDialog):
    def _get_python_version(self):
        """获取当前 Python 版本"""
        import sys
        version = sys.version_info
        return f"{version.major}.{version.minor}.{version.micro}"
    
    def _validate_package_name(self, name: str) -> tuple[bool, str]:
        """验证包名有效性"""
        import re
        
        # 拒绝纯数字名称
        if re.match(r'^\d+$', name):
            return False, f"无效的包名：'{name}'\n\n包名不能是纯数字"
        
        # PEP 503 包名模式验证
        if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?$|^[a-zA-Z0-9]$', name):
            return False, f"无效的包名：'{name}'\n\n包名只能包含字母、数字、下划线、连字符和点"
        
        return True, ""
    
    def _setup_ui(self):
        # 显示当前 Python 版本
        version_label = QLabel(
            f"💻 当前 Python 版本：{self.current_python_version}\n"
            f"⚠ 请确保外网 Python 版本与内网版本对齐（使用相同版本下载）"
        )
```

### 修复提交
- `3c32a43` - fix: QMenu import crash, dashboard initial refresh, and WHL download validation

### 预防指南
1. **PyQt6 模块划分**：
   - `QtWidgets`: QWidget, QPushButton, QLabel, QMenu, QAction (错！QAction 在 QtGui)
   - `QtGui`: QIcon, QFont, QPainter, QAction
   - `QtCore`: Qt, pyqtSignal, QObject, QTimer
   - 不确定时查阅官方文档或搜索确认

2. **初始化即刷新**：依赖外部数据（如数据库、配置文件）的 UI 组件，应在初始化完成后立即刷新一次

3. **输入验证**：用户输入的任何数据都应验证，尤其是：
   - 包名、文件名等标识符
   - 路径、URL 等资源定位符
   - 数字、日期等格式化数据

4. **版本兼容性提示**：涉及跨环境操作（如外网下载包到内网使用）时，应显示当前环境版本信息并提醒用户对齐全

---

## 2026-04-13:  Dashboard 首页脚本数量未实时更新、WPS 模块布局不直观、缺少 WHL 下载功能

### 问题描述
1. 首页 Dashboard 的脚本数量在增加/删除脚本后不会实时更新，需要切换页面后再回来才能看到正确数量
2. WPS 脚本模块使用下拉筛选来区分 Word/Excel，不够直观，用户希望能分开管理
3. Python 模块缺少下载离线 WHL 包的功能，用户需要手动到外网下载

### 根本原因
1. `_on_navigation_requested()` 方法中只在脚本变更时刷新 Dashboard，未在切换回 Dashboard 页面时刷新
2. WPS 模块使用单一列表 + filter_combo 的设计，Word 和 Excel 脚本混在一起
3. Python 模块未集成 `pip download` 功能

### 修复方式

**1. Dashboard 实时刷新**

在 `ui/main_window.py` 中：
```python
def _on_navigation_requested(self, name):
    # ... existing code ...
    
    # Refresh dashboard when switching to dashboard page
    if index == 0:
        self._refresh_dashboard()
```

**2. WPS 模块分 Tab 管理**

在 `ui/modules/wps_module.py` 中：
```python
# 使用 QTabWidget 替代 filter_combo
self.main_tabs = QTabWidget()

# Word tab
self.word_list = QListWidget()
self.main_tabs.addTab(word_widget, "Word")

# Excel tab
self.excel_list = QListWidget()
self.main_tabs.addTab(excel_widget, "Excel")

# 新增按钮添加下拉菜单支持
from PyQt6.QtGui import QMenu
self.add_menu = QMenu(self)
self.add_menu.addAction("默认功能区", lambda: self._on_add_script(""))
self.add_menu.addAction("新建功能区...", lambda: self._on_add_script("new"))
# 动态添加已有功能区
for group in sorted(groups):
    self.add_menu.addAction(f"→ {group}", lambda g=group: self._on_add_script(g))
```

**3. WHL 下载功能**

在 `ui/modules/python_module.py` 中：
```python
# 新增 WheelDownloadDialog 类
class WheelDownloadDialog(QDialog):
    def __init__(self, parent=None):
        # 包名输入框
        self.pkg_input = QLineEdit()
        # 路径选择框（带浏览按钮）
        self.path_input = QLineEdit()
        # 从 config 加载上次使用的路径
        self._load_last_path()
        
    def _on_download(self):
        # 保存路径到 config
        self._save_last_path(download_path)
        self.accept()

# 新增 _on_download_whl 方法
def _on_download_whl(self):
    dialog = WheelDownloadDialog(self)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        # 显示版本兼容性警告
        QMessageBox.warning(...)
        # 执行 pip download
        subprocess.run(["pip", "download", "-d", download_path, package_name])
```

### 修复提交
- `efcad81` - feat: dashboard stats refresh, WPS tabs, and WHL download

### 预防指南
1. **状态同步**：当用户切换到某个页面时，应刷新该页面的数据显示
2. **分类管理**：对于有明显分类的数据（如 Word/Excel），使用 Tab 比筛选下拉更直观
3. **记住用户偏好**：如下载路径等常用设置，应保存到 config 中方便下次使用
4. **重要提醒**：涉及外网操作（如下载包）时，应提前提醒用户注意事项（如版本兼容性）

---

## 2026-04-12: WPS 功能区预览不直观且一键部署未复制文件

### 问题描述
1. WPS 脚本模块的"预览功能区"按钮仅显示 XML 代码，用户无法直观看到 Ribbon 界面效果
2. 点击"一键部署"按钮后，生成的模板文件未复制到 WPS 启动目录

### 根本原因
1. `_on_preview_ribbon()` 方法仅调用 `generate_ribbon_xml()` 并在 QTextEdit 中显示 XML
2. `DeploymentService.deploy_all()` 只创建模板文件，未执行复制到启动目录的操作

### 修复方式

**1. 添加可视化 Ribbon 预览**

在 `ui/modules/wps_module.py` 中：
```python
# 新增 _render_ribbon_mockup 方法
def _render_ribbon_mockup(self, target_app: str):
    """渲染 WPS Ribbon UI 可视化 mockup"""
    # 创建 Tab 栏 mockup（蓝色背景，高亮"脚本管理器"tab）
    tab_bar = QFrame()
    tab_bar.setStyleSheet("background-color: #0078D4;")
    
    # 为每个脚本组创建GroupBox，内含按钮
    for group_name, scripts in groups.items():
        group_box = QGroupBox(group_name)
        for script in scripts:
            btn = QPushButton(script.get("ribbon_label", script["name"]))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #e8f4fc;
                    border: 1px solid #b8d4e8;
                    color: #0078D4;
                }
            """)
```

**2. 修复一键部署功能**

在 `core/deployment_service.py` 中：
```python
def _deploy_word_template(self) -> bool:
    """部署 WPS Word 模板"""
    # 先创建模板
    template_path = self.wps_service.create_word_template()
    if not template_path:
        return False
    
    # 如果配置了启动目录，复制过去
    if self.wps_service.word_startup and os.path.exists(self.wps_service.word_startup):
        dest = os.path.join(self.wps_service.word_startup, os.path.basename(template_path))
        with open(template_path, 'rb') as src:
            with open(dest, 'wb') as dst:
                dst.write(src.read())
    return True
```

**3. MainWindow 处理部署请求**

在 `ui/main_window.py` 中：
```python
def _on_deploy_requested(self):
    """处理部署按钮点击"""
    if not self.deployment_service:
        QMessageBox.warning(self, "警告", "部署服务未初始化")
        return
    
    result = self.deployment_service.deploy_all()
    
    # 显示部署结果
    messages = []
    if result['wps_word']:
        messages.append("✓ Word 模板已部署")
    # ...
```

### 修复提交
- `d584e2c` - feat: add visual WPS ribbon preview and fix one-click deploy

### 预防指南
1. **UI 预览应直观**：对于视觉相关的功能（如 Ribbon UI），应提供可视化预览而非仅显示代码
2. **部署=创建 + 复制**：一键部署不仅要生成文件，还要放到目标位置
3. **服务职责分离**：WpsService 负责创建模板，DeploymentService 负责部署到目标位置
4. **信号处理要在初始化前**：`_setup_system_tray()` 必须在 `_connect_signals()` 之前调用

---

## 2026-04-12: 配置路径未加载导致脚本不显示

### 问题描述
用户在设置中配置了脚本目录（如 `D:/ScriptNexus/scripts/python`），但 Python 脚本模块中不显示脚本。

### 根本原因
`MainWindow.__init__()` 使用硬编码的默认路径，未从 `ConfigService` 加载用户配置的路径。

### 修复方式
在 `set_services()` 中调用 `_load_paths_from_config()`，从配置中加载路径：
```python
def _load_paths_from_config(self):
    if not self.config_service:
        return
    scripts_dir = self.config_service.get("paths.scripts_dir", "")
    if scripts_dir and scripts_dir.strip():
        self.scripts_dir = scripts_dir
```

### 修复提交
- `ea5236a` - feat: load paths from config on MainWindow initialization

### 预防指南
1. **配置优先原则**：用户配置的路径应优先于默认路径
2. **初始化顺序**：先加载配置，再初始化依赖路径的组件
3. **路径一致性**：应用启动后应始终使用配置路径

---

## 2026-04-12: Python 脚本树形列表不显示脚本

### 问题描述
数据库中有脚本数据，但 Python 脚本模块的树形列表显示为空（0 个条目）。

### 根本原因
`_add_tree_items()` 方法中创建 `QTreeWidgetItem(parent_item)` 时，当 `parent_item=None`，项没有添加到树形控件中。

```python
# 错误代码
tree_item = QTreeWidgetItem(parent_item)  # parent=None 时，项是孤儿

# 正确代码
tree_item = QTreeWidgetItem()
if parent_item is None:
    self.tree_widget.addTopLevelItem(tree_item)  # 显式添加到根
else:
    parent_item.addChild(tree_item)  # 添加到父节点
```

### 修复提交
- `385f0f8` - fix: Python script tree not displaying scripts

### 预防指南
1. **Qt 树形控件添加入口**：必须显式调用 `addTopLevelItem()` 或 `addChild()`
2. **创建项时不要传 parent**：避免隐式依赖，显式添加更清晰
3. **测试时检查 UI 组件**：不仅检查数据，还要检查 UI 是否渲染

---

## 2026-04-12: 路径处理问题导致设置保存闪退

### 问题描述
通过设置界面修改路径后点击保存，应用闪退。

### 错误堆栈
```
File "ui/main_window.py", line 279, in _on_settings_requested
    self._reload_paths_from_config()
File "ui/main_window.py", line 292, in _reload_paths_from_config
    self.set_paths(scripts_dir, whl_pool_dir, templates_dir)
File "ui/main_window.py", line 91, in set_paths
    self.wps_module.set_templates_dir(templates_dir)
File "ui/modules/wps_module.py", line 593, in set_templates_dir
    self.wps_service.set_paths(path, None, None)
File "services/wps_service.py", line 57, in set_paths
    os.makedirs(templates_dir)
FileNotFoundError: [WinError 3] 系统找不到指定的路径。: ''
```

### 根本原因
多个 Service 类在处理路径参数时未验证空字符串，直接调用 `os.makedirs('')` 导致失败。

### 受影响的服务
| 服务 | 方法 | 修复方式 |
|------|------|----------|
| DependencyService | `__init__` | 添加 `if whl_dir and not os.path.exists(whl_dir)` |
| WpsService | `set_paths` | 添加 `if templates_dir and templates_dir.strip()` |
| JsService | `set_chrome_path` | 添加 `if path and path.strip()` |
| PythonService | `sync_scripts_from_dir` | 已有检查（未受影响） |

### 修复提交
- `27ae3ac` - fix: crash when clicking navigation buttons
- `a04807e` - fix: handle empty paths in WpsService and JsService

### 预防指南
1. **所有路径参数必须验证**：`if path and path.strip()` 是标配
2. **os.makedirs 前必须检查**：路径非空 + 目录不存在
3. **统一路径处理工具函数**：考虑创建 `utils/path_utils.py`
4. **设置保存前的路径验证**：SettingsDialog 应在保存前验证路径有效性

---

## 2026-04-12: 导航按钮点击闪退（多点故障）

### 问题描述
点击 "Python 脚本"、"WPS 脚本"、"JS 脚本" 按钮时应用闪退。

### 多个问题叠加
| 问题 | 文件 | 错误类型 | 描述 |
|------|------|----------|------|
| 变量名大小写 | `nav_bar.py:101` | `NameError` | `Name` 应为 `name` |
| 空路径处理 | `dependency_service.py:59` | `FileNotFoundError` | `os.makedirs('')` |
| 默认路径缺失 | `main_window.py` | `AttributeError` | `whl_pool_dir` 为 `None` |
| 表结构不一致 | `python_service.py` | `IntegrityError` | 缺少 `script_type` 字段 |

### 修复提交
- `bd8316b` - fix: move QAction import from QtWidgets to QtGui
- `27ae3ac` - fix: crash when clicking navigation buttons

### 经验教训
1. **Python 区分大小写**：变量命名后必须检查引用一致性
2. **表结构集中管理**：避免多处创建同一表，应统一使用 `ScriptModel`
3. **默认值优于 None**：路径参数应设置默认路径而非 `None`
4. **提交前运行完整测试**：292 个测试应全部通过

---

## 2026-04-10: SystemTray 图标为空导致 crash

### 问题描述
启动应用后点击导航按钮，后台报错 `QSystemTrayIcon::setVisible: No Icon set`

### 原因
`SystemTray._setup_icon()` 创建了空的 `QIcon()`

### 修复
使用 `QStyle.StandardPixmap.SP_DesktopIcon` 获取系统标准图标

### 经验教训
- 系统托盘图标必须验证有效性
- 不要使用空的 `QIcon()`

---

## 2026-04-10: NavBar 信号无限递归

### 问题描述
点击导航按钮后应用无响应，信号无限循环

### 原因
`navigate_to()` 方法中调用了 `navigation_requested.emit()`，而该信号又触发 `navigate_to()`

### 修复
移除 `navigate_to()` 中的信号发射，该方法仅用于程序化调用

### 经验教训
- 方法名加前缀区分用户触发/程序触发
- 信号连接应避免循环引用

---

## 2026-04-12: QAction 导入错误

### 问题描述
导入 `PythonModule` 时报错 `ImportError: cannot import name 'QAction' from 'PyQt6.QtWidgets'`

### 原因
PyQt6 中 `QAction` 在 `QtGui` 模块，而非 `QtWidgets`

### 修复
```python
# 错误
from PyQt6.QtWidgets import QAction

# 正确
from PyQt6.QtGui import QAction
```

### 经验教训
- PyQt6 模块划分与 PyQt5 不同
- 常见类所属模块：
  - `QtWidgets`: QWidget, QPushButton, QLabel, etc.
  - `QtGui`: QIcon, QFont, QAction, QPainter, etc.
  - `QtCore`: Qt, pyqtSignal, QObject, QTimer, etc.

---

## 检查清单（提交前必查）

### 代码质量
- [ ] 变量名大小写一致性检查
- [ ] 所有路径参数有空值验证
- [ ] os.makedirs/os.path.exists 前检查路径非空
- [ ] 导入语句来源正确（尤其是 PyQt6）

### 数据库
- [ ] 表结构定义与 ScriptModel 一致
- [ ] INSERT 语句包含所有 NOT NULL 字段
- [ ] 多服务共用表只在一个地方创建

### 测试
- [ ] 运行完整测试套件（292 tests）
- [ ] 手动测试 UI 导航流程
- [ ] 手动测试设置保存流程

### UI/UX
- [ ] 系统托盘图标有效
- [ ] 信号连接无循环
- [ ] 错误提示友好（中文）
