# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for ScriptNexus Windows executable."""

import os
import sys

block_cipher = None

# Get project root (where spec file is located)
PROJECT_ROOT = os.path.dirname(os.path.abspath(SPEC))

# Data files to include in the bundle
datas = [
    # Templates directory (read-only)
    (os.path.join(PROJECT_ROOT, 'templates'), 'templates'),
    # Default config file
    (os.path.join(PROJECT_ROOT, 'data', 'config.json'), 'data'),
    # Icons
    (os.path.join(PROJECT_ROOT, 'pics', 'icon.ico'), 'pics'),
    (os.path.join(PROJECT_ROOT, 'pics', 'icon.png'), 'pics'),
]

# Hidden imports for PyQt6 and other dependencies
hiddenimports = [
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'PyQt6.sip',
    'sqlite3',
    'json',
    'docx',
    'openpyxl',
    'zipfile',
    'shutil',
    'glob',
    'datetime',
    'typing',
]

# Excludes to reduce package size
excludes = [
    'tkinter',
    'unittest',
    'pytest',
    'IPython',
    'jupyter',
    'matplotlib',
    'numpy',
    'pandas',
    'scipy',
    'PIL',
    'cv2',
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
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ScriptNexus',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI application, no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(PROJECT_ROOT, 'pics', 'icon.ico'),
)