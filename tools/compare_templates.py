"""Compare VBA template structures for debugging."""

import sys
import os
import zipfile
import hashlib

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def analyze_template(template_path: str) -> dict:
    """Analyze a template file structure."""
    if not os.path.exists(template_path):
        return {'error': f'File not found: {template_path}'}

    result = {
        'file': os.path.basename(template_path),
        'size': os.path.getsize(template_path),
        'files': {},
        'vba_project_bin': None,
    }

    try:
        with zipfile.ZipFile(template_path, 'r') as zf:
            for name in sorted(zf.namelist()):
                info = zf.getinfo(name)
                data = zf.read(name)
                result['files'][name] = {
                    'size': info.file_size,
                    'md5': hashlib.md5(data).hexdigest()[:8],
                }

                # Check for vbaProject.bin
                if 'vbaProject.bin' in name:
                    result['vba_project_bin'] = {
                        'path': name,
                        'size': len(data),
                        'md5': hashlib.md5(data).hexdigest(),
                        'header': data[:8].hex(),
                    }

                    # Try to parse as OLE
                    try:
                        import olefile
                        ole = olefile.OleFileIO(io.BytesIO(data))
                        streams = []
                        for entry in ole.listdir():
                            stream_name = '/'.join(entry)
                            try:
                                stream_data = ole.openstream(stream_name).read()
                                streams.append({
                                    'name': stream_name,
                                    'size': len(stream_data),
                                })
                            except:
                                streams.append({'name': stream_name, 'size': 0})
                        ole.close()
                        result['vba_project_bin']['streams'] = streams
                    except Exception as e:
                        result['vba_project_bin']['ole_error'] = str(e)
    except Exception as e:
        result['error'] = str(e)

    return result


def main():
    """Main entry point."""
    print("=" * 70)
    print("VBA Template Structure Comparison Tool")
    print("=" * 70)
    print()

    # Common paths
    paths_to_check = [
        # Word startup directory
        r'C:\Users\L\AppData\Roaming\Kingsoft\WPS Office\startup\wps',
        # Excel startup directory
        r'D:\WPS Office\12.1.0.25225\office6\XLSTART',
        # Templates directory
        r'D:\ScriptNexus\templates',
    ]

    print("Scanning directories...\n")

    all_templates = []
    for base_dir in paths_to_check:
        if not os.path.exists(base_dir):
            print(f"Directory not found: {base_dir}")
            continue

        for f in os.listdir(base_dir):
            if f.endswith('.dotm') or f.endswith('.xlam'):
                full_path = os.path.join(base_dir, f)
                all_templates.append({
                    'dir': base_dir,
                    'path': full_path,
                    'name': f,
                })
                print(f"Found: {f} in {base_dir}")

    if not all_templates:
        print("\nNo template files found!")
        return

    print(f"\n{'=' * 70}\n")

    # Analyze each template
    for tmpl in all_templates:
        print(f"--- {tmpl['name']} ---")
        print(f"Path: {tmpl['path']}")

        result = analyze_template(tmpl['path'])

        if 'error' in result:
            print(f"Error: {result['error']}")
        else:
            print(f"Size: {result['size']} bytes")
            print(f"Files: {len(result['files'])}")

            if result['vba_project_bin']:
                vba = result['vba_project_bin']
                print(f"\nvbaProject.bin:")
                print(f"  Path: {vba['path']}")
                print(f"  Size: {vba['size']} bytes ({vba['size']/1024:.1f} KB)")
                print(f"  MD5: {vba['md5']}")
                print(f"  Header: {vba['header']}")

                if 'streams' in vba:
                    print(f"\n  OLE Streams ({len(vba['streams'])}):")
                    for stream in vba['streams']:
                        print(f"    {stream['name']}: {stream['size']} bytes")
            else:
                print("\n  NO vbaProject.bin found!")

        print("\n")


if __name__ == '__main__':
    main()
