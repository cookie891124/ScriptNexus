# ScriptNexus

A PyQt6 desktop application for managing and deploying scripts across WPS Office, Python, and JavaScript.

## Development Requirements

- Python 3.10+
- PyQt6 >= 6.4.0
- python-docx >= 0.8.11
- openpyxl >= 3.0.0

## Build

After any feature change, build the Windows executable:

```bash
build_windows.bat
```

Or manually:

```bash
python -m PyInstaller scriptnexus.spec --distpath dist --workpath build --noconfirm
```

The output will be in `dist/ScriptNexus.exe`.
