# ScriptNexus 部署打包指南

随着项目增长，每次压缩整个文件夹变得越来越慢。本项目提供了两种打包方案：

## 方案对比

| 方案 | 适用场景 | 优点 | 文件大小示例 |
|------|----------|------|-------------|
| **完整打包** | 首次部署、内网环境重置 | 简单可靠，包含所有文件 | ~16MB |
| **增量打包** | 日常开发测试 | 只打包变更文件，极快 | ~5KB |

---

## 快速开始

### 1. 首次部署（完整打包）

```bash
# 在内网外部的开发机上执行
cd D:\ScriptNexus
python tools/package_deploy.py --no-tests
```

生成的文件如：`ScriptNexus_deploy_20260415_135413_no_tests.zip`

**特点**：
- 自动排除 `__pycache__`、`.git`、`*.db`、`*.log` 等临时文件
- 可选排除测试文件（`--no-tests`）
- 压缩率约 60-70%

---

### 2. 日常更新（增量打包）

```bash
# 第一次：创建基准包
python tools/package_incremental.py --init

# 之后每次：只打包变更的文件
python tools/package_incremental.py
```

生成的文件如：`ScriptNexus_increment_20260415_135441.zip`

**在内网应用更新**：
```bash
cd /path/to/ScriptNexus
python tools/package_incremental.py --apply ScriptNexus_increment_20260415_135441.zip --target .
```

---

## 命令参考

### package_deploy.py - 完整打包

```bash
# 列出将要打包的文件（不创建压缩包）
python tools/package_deploy.py --list-files

# 创建完整部署包（排除测试文件）
python tools/package_deploy.py --no-tests

# 创建完整部署包（包含测试文件）
python tools/package_deploy.py

# 指定输出文件名
python tools/package_deploy.py -o my-deploy.zip
```

### package_incremental.py - 增量打包

```bash
# 创建完整基准包（仅首次需要）
python tools/package_incremental.py --init

# 创建增量包（只包含变更文件）
python tools/package_incremental.py

# 查看当前状态
python tools/package_incremental.py --show-state

# 在内网应用增量包
python tools/package_incremental.py --apply ScriptNexus_increment_xxx.zip --target .
```

---

## 排除的文件类型

以下文件和目录会自动被排除：

| 类型 | 示例 |
|------|------|
| Python 缓存 | `__pycache__/`, `*.pyc`, `*.pyo` |
| Git 仓库 | `.git/` |
| 测试缓存 | `.pytest_cache/` |
| IDE 配置 | `.idea/`, `.vscode/` |
| 虚拟环境 | `venv/`, `.venv/`, `env/` |
| 数据库文件 | `*.db` |
| 日志文件 | `*.log` |
| 备份文件 | `*.bak`, `*.orig` |

---

## 推荐工作流

### 首次部署
```bash
# 开发机
python tools/package_deploy.py --no-tests

# 将生成的 .zip 文件复制到内网
# 在内网解压
unzip ScriptNexus_deploy_xxx.zip -d ScriptNexus/
```

### 日常开发
```bash
# 开发机 - 每天或每次重大修改后
python tools/package_incremental.py

# 将生成的 increment_xxx.zip 复制到内网

# 内网 - 应用更新
python tools/package_incremental.py --apply increment_xxx.zip --target .
```

### 重置内网环境
```bash
# 如果内网环境出现问题，可以删除后重新完整部署
# 删除旧文件
rm -rf ScriptNexus/*

# 重新解压完整包
unzip ScriptNexus_full_xxx.zip

# 重新初始化状态
python tools/package_incremental.py --init
```

---

## 效果对比

| 操作 | 传统方式（全量压缩） | 推荐方式 | 节省 |
|------|---------------------|----------|------|
| 首次部署 | ~20MB | ~16MB | 20% |
| 日常更新 | ~20MB | ~5KB | 99.97% |
| 传输时间 | ~30 秒 | <1 秒 | 99%+ |

---

## 故障排查

### 问题：增量包应用失败
**解决**：重新创建完整包并初始化
```bash
# 开发机
python tools/package_incremental.py --init

# 内网
# 删除旧文件后重新解压完整包
```

### 问题：打包后文件过大
**解决**：检查是否有大文件未被排除
```bash
# 查看将要打包的文件列表
python tools/package_deploy.py --list-files

# 手动删除不需要的大文件
```

### 问题：状态文件丢失
**解决**：重新初始化
```bash
python tools/package_incremental.py --init
```

---

## 技术细节

- **增量检测**：使用 MD5 哈希值检测文件变更
- **状态存储**：`.deploy_state.json` 记录上次打包状态
- **原子操作**：增量包应用是原子的，失败不会影响现有文件

---

## 自动化建议

可以添加批处理脚本简化操作：

```batch
@echo off
REM deploy.bat - 快速打包脚本
cd /d %~dp0
echo Creating deployment package...
python tools/package_deploy.py --no-tests
pause
```

```batch
@echo off
REM increment.bat - 快速增量打包
cd /d %~dp0
echo Creating incremental package...
python tools/package_incremental.py
pause
```
