#!/usr/bin/env python
"""Check WPS Trust Center settings for VBA access.

Run this to check if there's a setting blocking VBA COM access.
"""

import sys
import os

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 70)
print("WPS Trust Center Settings Check")
print("=" * 70)
print()

print("Please manually check the following in WPS Office:")
print()
print("1. In WPS Word, go to:")
print("   文件 -> 选项 -> 信任中心 -> 信任中心设置")
print()
print("2. Check these settings:")
print("   a. 宏设置 -> 确保 '信任 VBA 项目的对象模型' is checked")
print("   b. 隐私选项 -> 确保 '应用程序增强' is enabled")
print()
print("3. If using WPS Enterprise, check with IT if Group Policy")
print("   restricts COM access to VBA projects")
print()
print("=" * 70)

# Also check if there's a way to enable it programmatically
print("\nChecking registry for WPS trust settings...")

if sys.platform == 'win32':
    try:
        import winreg
    except ImportError:
        print("Cannot access registry")
        sys.exit(1)

    # Check HKCU for WPS settings
    wps_paths = [
        r"SOFTWARE\Kingsoft\Office 6.0\Common\Security",
        r"SOFTWARE\Kingsoft\Office 6.0\Word\Security",
        r"SOFTWARE\WOW6432Node\Kingsoft\Office 6.0\Common\Security",
    ]

    for path in wps_paths:
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, path)
            print(f"\nFound: {path}")
            try:
                i = 0
                while True:
                    name, value, _ = winreg.EnumValue(key, i)
                    print(f"  {name} = {value}")
                    i += 1
            except WindowsError:
                pass
            winreg.CloseKey(key)
        except WindowsError:
            pass

print()
print("=" * 70)
print("If Trust Center settings look correct but VBA still fails,")
print("try running WPS as Administrator and then running the deploy.")
print("=" * 70)
