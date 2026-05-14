#!/usr/bin/env python
"""Check and configure WPS Office Trust Center settings for VBA.

This script checks if WPS is configured to allow COM access to VBA projects.
"""

import sys
import os

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 70)
print("WPS Trust Center and VBA Access Configuration")
print("=" * 70)
print()

# Check if we're on Windows
if sys.platform != 'win32':
    print("This script only works on Windows")
    sys.exit(1)

# Try to check WPS registry settings
print("[1] Checking WPS registry settings...")

try:
    import winreg
except ImportError:
    print("    winreg not available")
    sys.exit(1)

# WPS Registry locations to check
wps_keys = [
    r"SOFTWARE\Kingsoft\Office 6.0",
    r"SOFTWARE\WOW6432Node\Kingsoft\Office 6.0",
    r"SOFTWARE\Kingsoft\WPS Office",
    r"SOFTWARE\WOW6432Node\Kingsoft\WPS Office",
]

vba_settings = {}

for key_path in wps_keys:
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path)
        print(f"    Found registry key: {key_path}")
        winreg.CloseKey(key)
        vba_settings[key_path] = True
    except WindowsError:
        pass

if not vba_settings:
    print("    No WPS registry keys found in HKLM")

# Check current user settings
print("\n[2] Checking user-level WPS settings...")
user_keys = [
    r"SOFTWARE\Kingsoft\Office 6.0",
    r"SOFTWARE\WOW6432Node\Kingsoft\Office 6.0",
    r"SOFTWARE\Kingsoft\WPS Office",
    r"SOFTWARE\WOW6432Node\Kingsoft\WPS Office",
]

for key_path in user_keys:
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path)
        print(f"    Found registry key: {key_path}")
        winreg.CloseKey(key)
    except WindowsError:
        pass

# Check specific VBA trust settings
print("\n[3] Checking VBA Trust Center settings...")

trust_keys = [
    r"SOFTWARE\Microsoft\Office\16.0\Word\Resiliency\DocumentStyles",
    r"SOFTWARE\Kingsoft\Office 6.0\Word\Resiliency",
]

for key_path in trust_keys:
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path)
        print(f"    Found: {key_path}")
        try:
            i = 0
            while True:
                name, value, _ = winreg.EnumValue(key, i)
                print(f"      {name} = {value}")
                i += 1
        except WindowsError:
            pass
        winreg.CloseKey(key)
    except WindowsError:
        print(f"    Not found: {key_path}")

# Check WPS Options
print("\n[4] Checking WPS Options for VBA settings...")
options_keys = [
    r"SOFTWARE\Kingsoft\Office 6.0\Options",
    r"SOFTWARE\WOW6432Node\Kingsoft\Office 6.0\Options",
]

for key_path in options_keys:
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path)
        print(f"    Found: {key_path}")

        # Check for VBA-related settings
        vba_related = ['VBA', 'Macro', 'Security', 'Trust', 'COM']
        try:
            i = 0
            while True:
                name, value, _ = winreg.EnumValue(key, i)
                if any(r.lower() in name.lower() for r in vba_related):
                    print(f"      {name} = {value}")
                i += 1
        except WindowsError:
            pass
        winreg.CloseKey(key)
    except WindowsError:
        pass

# Try to check if there's a trust center setting
print("\n[5] Summary and Recommendations...")
print("""
Based on testing, WPS Office appears to block COM access to VBA projects.

Possible solutions:

1. Enable VBA in WPS Trust Center:
   - Open WPS Word
   - Go to: 文件 -> 选项 -> 信任中心 -> 信任中心设置
   - Enable "信任 VBA 项目的对象模型"

2. Or, use a different deployment method that doesn't require COM VBA access

3. Check if there's a Group Policy setting blocking this

4. Try running WPS as Administrator
""")

print("=" * 70)
