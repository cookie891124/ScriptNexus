# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for ScriptNexus Linux/Kylin executable."""

import os
import sys

block_cipher = None

PROJECT_ROOT = os.path.dirname(os.path.abspath(SPEC))

# Data files for Linux
datas = []
_config_json = os.path.join(PROJECT_ROOT, 'data', 'config.json')
_config_example = os.path.join(PROJECT_ROOT, 'data', 'config.example.json')
if os.path.exists(_config_json):
    datas.append((_config_json, 'data'))
elif os.path.exists(_config_example):
    datas.append((_config_example, 'data'))

_templates = os.path.join(PROJECT_ROOT, 'templates')
if os.path.exists(_templates):
    datas.append((_templates, 'templates'))

_icon = os.path.join(PROJECT_ROOT, 'pics', 'icon.png')
if os.path.exists(_icon):
    datas.append((_icon, 'pics'))

hiddenimports = [
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'PyQt6.sip',
    'sqlite3',
    'json',
    'docx',
    'openpyxl',
]

excludes = [
    'tkinter',
    'unittest',
    'pytest',
    'IPython',
    'jupyter',
    'matplotlib',
    'numpy',
    'pandas',
]

a = Analysis(
    [os.path.join(PROJECT_ROOT, 'app.py')],
    pathex=[PROJECT_ROOT],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[os.path.join(PROJECT_ROOT, 'hooks')],
    hooksconfig={},
    runtime_hooks=[os.path.join(PROJECT_ROOT, 'hooks', 'runtime_hook.py')],
    excludes=excludes,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ScriptNexus',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    console=False,
    target_arch='x86_64',  # x86_64 for most enterprise Kylin; arm64 for Kirin/Feiteng chips
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ScriptNexus',
)
