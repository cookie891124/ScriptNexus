#!/usr/bin/env python
"""Test WPS specific capabilities - check what COM properties are available.

Run this to see what WPS Office actually supports.
"""

import sys
import os

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 70)
print("WPS Office COM Capabilities Test")
print("=" * 70)
print()

import win32com.client
from pythoncom import DISPATCH_PROPERTYGET

# Connect to WPS
print("[1] Connecting to WPS Word...")
try:
    word = win32com.client.Dispatch('Kwps.Application')
    word.Visible = False
    print("    OK: Connected")
except Exception as e:
    print(f"    FAILED: {e}")
    sys.exit(1)

# Create document
print("\n[2] Creating document...")
try:
    doc = word.Documents.Add()
    print(f"    OK: {doc.Name}")
except Exception as e:
    print(f"    FAILED: {e}")
    word.Quit()
    sys.exit(1)

# Try different properties to understand WPS capabilities
print("\n[3] Testing various document properties...")

properties_to_test = [
    ('VBProject', 'VBA Project'),
    ('CodeProject', 'Code Project'),
    ('HasVBProject', 'Has VBA Project'),
    ('Macros', 'Macros'),
    ('Parent', 'Parent'),
    ('CustomDocumentProperties', 'Custom Properties'),
]

for prop_name, description in properties_to_test:
    try:
        # Try to get the property
        result = getattr(doc, prop_name)
        print(f"    {prop_name}: EXISTS (value: {type(result).__name__})")
    except AttributeError:
        print(f"    {prop_name}: NOT AVAILABLE (AttributeError)")
    except Exception as e:
        error_code = e.args[0] if e.args else "Unknown"
        print(f"    {prop_name}: ERROR - {error_code}")

# Try to check if document has VB support
print("\n[4] Checking document type...")
try:
    print(f"    Document type: {doc.Type}")
    print(f"    Document name: {doc.Name}")
    print(f"    Document path: {doc.Path}")
except Exception as e:
    print(f"    Error: {e}")

# Try to see what VBComponents gives us
print("\n[5] Testing VBComponents access...")
try:
    vbc = doc.VBProject.VBComponents
    print(f"    VBComponents count: {vbc.Count}")
except Exception as e:
    error_code = e.args[0] if e.args else "Unknown"
    print(f"    VBComponents access failed: {error_code}")

# Cleanup
print("\n[6] Cleaning up...")
try:
    doc.Close(False)
except:
    pass
try:
    word.Quit()
except:
    pass

print("\n" + "=" * 70)
print("Test completed. Please share the output with the developer.")
print("=" * 70)
