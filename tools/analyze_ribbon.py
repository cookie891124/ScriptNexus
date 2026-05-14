"""Extract ribbon customization info from VBA project."""

import sys
import os
import zipfile

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def extract_ribbon_info(template_path: str) -> None:
    """Extract ribbon customization from a template file."""
    if not os.path.exists(template_path):
        print(f"File not found: {template_path}")
        return

    print(f"=== Analyzing: {template_path} ===\n")

    try:
        with zipfile.ZipFile(template_path, 'r') as zf:
            # Check for customUI folder
            namelist = zf.namelist()

            # Look for Ribbon customizations
            customui_files = [n for n in namelist if 'customUI' in n.lower()]

            if customui_files:
                print("Ribbon Customization Files:")
                for f in customui_files:
                    print(f"  - {f}")
                    try:
                        content = zf.read(f).decode('utf-8', errors='ignore')
                        print(f"    Content preview ({len(content)} chars):")
                        # Print first 500 chars of XML
                        lines = content.split('\n')[:20]
                        for line in lines:
                            print(f"      {line}")
                        if len(content.split('\n')) > 20:
                            print("      ...")
                    except Exception as e:
                        print(f"    Error reading: {e}")
                print()

            # Check VBA modules for ribbon callbacks
            vba_files = [n for n in namelist if n.lower().startswith('vba/') and n.endswith('.bas')]

            if vba_files:
                print("VBA Modules:")
                for f in vba_files:
                    print(f"\n  --- {f} ---")
                    try:
                        content = zf.read(f).decode('utf-8', errors='ignore')
                        lines = content.split('\n')

                        # Look for Sub declarations
                        for i, line in enumerate(lines):
                            if 'Sub ' in line and '(' in line:
                                # Print the Sub and next few lines
                                snippet = '\n'.join(lines[i:i+3])
                                print(f"    {snippet}")
                    except Exception as e:
                        print(f"    Error reading: {e}")
                print()

            # Check vbaProject.bin for embedded ribbon info
            vba_bin_paths = [n for n in namelist if 'vbaProject.bin' in n]
            if vba_bin_paths:
                print("vbaProject.bin Analysis:")
                for bin_path in vba_bin_paths:
                    data = zf.read(bin_path)
                    print(f"  File: {bin_path}")
                    print(f"  Size: {len(data)} bytes")

                    # Try to find ribbon-related strings
                    try:
                        import olefile
                        ole = olefile.OleFileIO(io.BytesIO(data))
                        for entry in ole.listdir():
                            stream_name = '/'.join(entry)
                            if 'ribbon' in stream_name.lower() or 'menu' in stream_name.lower():
                                try:
                                    stream_data = ole.openstream(stream_name).read()
                                    # Try to decode as text
                                    text = stream_data.decode('utf-8', errors='ignore')
                                    if text.strip():
                                        print(f"    {stream_name}: {len(stream_data)} bytes")
                                        # Print first 200 chars
                                        preview = text[:200].replace('\n', ' ')
                                        print(f"      Preview: {preview}...")
                                except:
                                    pass
                        ole.close()
                    except ImportError:
                        print("    (olefile not available, skipping OLE parsing)")
                    except Exception as e:
                        print(f"    Error: {e}")
                print()

    except Exception as e:
        print(f"Error: {e}")


def main():
    """Main entry point."""
    print("=" * 70)
    print("Ribbon Customization Analyzer")
    print("=" * 70)
    print()

    # Check Word templates
    word_dir = r'C:\Users\L\AppData\Roaming\Kingsoft\WPS Office\startup\wps'
    if os.path.exists(word_dir):
        print("=== WORD TEMPLATES ===\n")
        for f in sorted(os.listdir(word_dir)):
            if f.endswith('.dotm'):
                extract_ribbon_info(os.path.join(word_dir, f))

    # Check Excel templates
    excel_dir = r'D:\WPS Office\12.1.0.25225\office6\XLSTART'
    if os.path.exists(excel_dir):
        print("=== EXCEL TEMPLATES ===\n")
        for f in sorted(os.listdir(excel_dir)):
            if f.endswith('.xlam'):
                extract_ribbon_info(os.path.join(excel_dir, f))


if __name__ == '__main__':
    main()
