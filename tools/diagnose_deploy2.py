#!/usr/bin/env python
"""Diagnostic script v2 - tests if saving first helps.

Run this on the internal network to diagnose deployment problems.
"""

import sys
import os
import tempfile

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 70)
print("COM Deployment Diagnostic Tool v2")
print("=" * 70)
print()

import win32com.client

# Test: Create document, SAVE IT, then access VBProject
print("[Test] Create document -> Save -> Access VBProject")
print()

try:
    word = win32com.client.Dispatch('Kwps.Application')
    word.Visible = False
    print("[1] Created WPS Word instance")

    doc = word.Documents.Add()
    print(f"[2] Created document: {doc.Name}")

    # Save the document first
    temp_path = os.path.join(tempfile.gettempdir(), "test_vba_doc.dotm")
    doc.SaveAs(temp_path, 5)  # 5 = wdFormatTemplate
    print(f"[3] Saved document to: {temp_path}")

    # Now try to access VBProject
    print("[4] Attempting to access VBProject...")
    vb_project = doc.VBProject
    print(f"[5] SUCCESS! VBProject accessible")
    print(f"    Components: {vb_project.VBComponents.Count}")

    # Try to add a module
    print("[6] Attempting to add VBA module...")
    new_module = vb_project.VBComponents.Add(1)
    new_module.Name = "TestModule"
    print(f"[7] SUCCESS! Created module: {new_module.Name}")

    # Add code
    print("[8] Attempting to add VBA code...")
    test_code = "Sub Test()\n    MsgBox \"Hello\"\nEnd Sub"
    new_module.CodeModule.AddLines(test_code)
    print("[9] SUCCESS! Added VBA code")

    # Save again with VBA
    doc.Save()
    print(f"[10] Saved document with VBA")

    doc.Close(False)
    word.Quit()
    print("\nALL TESTS PASSED!")

except Exception as e:
    error_code = e.args[0] if e.args else "Unknown"
    print(f"\nFAILED at step with error: {e}")
    print(f"Error code: 0x{abs(error_code):08X}" if isinstance(error_code, int) else error_code)

    # Try to cleanup
    try:
        doc.Close(False)
    except:
        pass
    try:
        word.Quit()
    except:
        pass

print("\n" + "=" * 70)
