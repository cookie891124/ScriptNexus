#!/usr/bin/env python
"""Diagnostic script for COM deployment issues.

Run this on the internal network to diagnose deployment problems.
"""

import sys
import os
import traceback

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 70)
print("COM Deployment Diagnostic Tool")
print("=" * 70)
print()

# Step 1: Check pywin32
print("[1/6] Checking pywin32...")
try:
    import win32com.client
    print("  OK: pywin32 is installed")
except ImportError:
    print("  ERROR: pywin32 is not installed")
    print("  Please install: pip install pywin32")
    sys.exit(1)

# Step 2: Check WPS Word
print("\n[2/6] Checking WPS Word COM...")
word = None
try:
    word = win32com.client.GetActiveObject('Kwps.Application')
    print("  OK: Connected to existing WPS Word")
except Exception as e:
    try:
        word = win32com.client.Dispatch('Kwps.Application')
        print("  OK: Created new WPS Word instance")
    except Exception as e2:
        print(f"  ERROR: Cannot connect to WPS Word: {e2}")
        print("  Make sure WPS Office is installed")

if word is None:
    sys.exit(1)

# Step 3: Create a test document
print("\n[3/6] Creating test document...")
doc = None
try:
    doc = word.Documents.Add()
    print(f"  OK: Document created (name: {doc.Name})")
except Exception as e:
    print(f"  ERROR: Cannot create document: {e}")
    word.Quit()
    sys.exit(1)

# Step 4: Check VBProject
print("\n[4/6] Checking VBProject...")
vb_project = None
try:
    vb_project = doc.VBProject
    print(f"  OK: VBProject accessible")
    print(f"  Components: {vb_project.VBComponents.Count}")
except Exception as e:
    print(f"  ERROR: Cannot access VBProject: {e}")
    doc.Close(False)
    word.Quit()
    sys.exit(1)

# Step 5: List existing components
print("\n[5/6] Existing VBA components:")
try:
    for comp in vb_project.VBComponents:
        print(f"  - {comp.Name} (type: {comp.Type})")
except Exception as e:
    print(f"  ERROR: Cannot list components: {e}")

# Step 6: Try to create a module and add code
print("\n[6/6] Testing module creation and code injection...")
try:
    # Create a standard module (vbext_ct_StandardModule = 1)
    new_module = vb_project.VBComponents.Add(1)
    new_module.Name = "TestModule"
    print(f"  OK: Created module '{new_module.Name}'")

    # Simple VBA code
    test_code = """' Test module
Sub TestSub()
    MsgBox "Hello from diagnostic!"
End Sub
"""
    new_module.CodeModule.AddLines(test_code)
    print(f"  OK: Added {len(test_code)} characters of VBA code")

    # Verify
    line_count = new_module.CodeModule.CountOfLines
    print(f"  OK: Module now has {line_count} lines of code")

except Exception as e:
    print(f"  ERROR: {e}")
    print(f"  Error code: 0x{abs(e.args[0]):08X}" if e.args else "No error code")
    traceback.print_exc()

# Cleanup
print("\n" + "=" * 70)
print("Cleaning up...")
try:
    doc.Close(False)
except:
    pass
try:
    word.Quit()
except:
    pass
print("Done.")
print("=" * 70)
