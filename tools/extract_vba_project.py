"""Extract vbaProject.bin from WPS Office template files.

This script extracts vbaProject.bin from .xlsm, .xlam, .dotm, .docm files
so they can be used for deployment in environments without VBA editor access.

Usage:
    python extract_vba_project.py <template_file> [output_directory]

Examples:
    python extract_vba_project.py template.xlam
    python extract_vba_project.py template.dotm D:\output
    python extract_vba_project.py "C:\path\to\template.xlam" "D:\output dir"
"""

import os
import sys
import zipfile
import shutil
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def extract_vba_project(template_path: str, output_dir: str) -> bool:
    """Extract vbaProject.bin from a template file.

    Args:
        template_path: Path to the .xlsm, .xlam, .dotm, or .docm file
        output_dir: Directory to save the extracted vbaProject.bin

    Returns:
        True if successful, False otherwise
    """
    if not os.path.exists(template_path):
        print(f"ERROR: File not found: {template_path}")
        return False

    # Determine file type
    ext = os.path.splitext(template_path)[1].lower()
    file_type_map = {
        '.xlsm': 'Excel Macro-Enabled Workbook',
        '.xlam': 'Excel Add-In',
        '.dotm': 'Word Macro-Enabled Template',
        '.docm': 'Word Macro-Enabled Document',
    }

    if ext not in file_type_map:
        print(f"ERROR: Unsupported file type: {ext}")
        print(f"Supported types: {', '.join(file_type_map.keys())}")
        return False

    file_type = file_type_map[ext]

    # Determine VBA path based on file type
    vba_path_map = {
        '.xlsm': 'xl/vbaProject.bin',
        '.xlam': 'xl/vbaProject.bin',
        '.dotm': 'word/vbaProject.bin',
        '.docm': 'word/vbaProject.bin',
    }

    vba_bin_path = vba_path_map[ext]

    print(f"Processing: {os.path.basename(template_path)}")
    print(f"File type: {file_type}")
    print()

    try:
        with zipfile.ZipFile(template_path, 'r') as zf:
            # List all files (optional debug info)
            print("Files in archive:")
            for name in sorted(zf.namelist()):
                marker = " <-- VBA" if 'vba' in name.lower() else ""
                print(f"  {name}{marker}")
            print()

            # Check if vbaProject.bin exists
            if vba_bin_path not in zf.namelist():
                print(f"ERROR: {vba_bin_path} not found in archive!")
                print()
                print("This file may not contain VBA macros, or the VBA project")
                print("has not been initialized. Please add a macro to the file")
                print("first using the WPS VBA editor.")
                return False

            # Extract vbaProject.bin
            vba_bin = zf.read(vba_bin_path)

            # Create output filename
            base_name = os.path.splitext(os.path.basename(template_path))[0]
            if ext in ['.xlsm', '.xlam']:
                output_name = f'{base_name}_vbaProject.bin'
            else:
                output_name = f'{base_name}_vbaProject.bin'

            output_path = os.path.join(output_dir, output_name)

            # Write to file
            with open(output_path, 'wb') as f:
                f.write(vba_bin)

            print(f"SUCCESS: Extracted vbaProject.bin")
            print(f"  Output: {output_path}")
            print(f"  Size: {len(vba_bin)} bytes")

            return True

    except zipfile.BadZipFile:
        print(f"ERROR: {template_path} is not a valid ZIP file")
        print("Office files should be ZIP archives. This file may be corrupted")
        print("or in an older binary format (.xls, .doc instead of .xlsm, .docm)")
        return False
    except Exception as e:
        print(f"ERROR: Failed to extract vbaProject.bin: {e}")
        return False


def process_directory(input_dir: str, output_dir: str) -> dict:
    """Process all template files in a directory.

    Args:
        input_dir: Directory containing template files
        output_dir: Directory to save extracted vbaProject.bin files

    Returns:
        Dictionary with success/failure counts
    """
    results = {'success': 0, 'failed': 0, 'total': 0}

    if not os.path.exists(input_dir):
        print(f"ERROR: Directory not found: {input_dir}")
        return results

    # Find all template files
    extensions = ['.xlsm', '.xlam', '.dotm', '.docm']
    files = []
    for f in os.listdir(input_dir):
        if os.path.splitext(f)[1].lower() in extensions:
            files.append(os.path.join(input_dir, f))

    if not files:
        print(f"No template files found in: {input_dir}")
        print(f"Looking for: {', '.join(extensions)}")
        return results

    print(f"Found {len(files)} template file(s)")
    print()

    for file_path in files:
        results['total'] += 1
        if extract_vba_project(file_path, output_dir):
            results['success'] += 1
        else:
            results['failed'] += 1
        print()
        print("-" * 60)
        print()

    return results


def main():
    """Main entry point."""
    print("=" * 60)
    print("VBA Project Extractor")
    print("=" * 60)
    print()

    # Parse arguments
    if len(sys.argv) == 1:
        # Interactive mode - scan common WPS startup directories
        print("No arguments provided. Scanning common WPS startup directories...")
        print()

        candidate_dirs = [
            os.path.expandvars(r'%APPDATA%\Kingsoft\WPS Office\startup'),
            os.path.expandvars(r'%APPDATA%\Kingsoft\WPS Office\*\addons'),
            r'C:\Program Files (x86)\Kingsoft\WPS Office\addons',
        ]

        all_files = []
        for candidate in candidate_dirs:
            if os.path.exists(candidate):
                for f in os.listdir(candidate):
                    if os.path.splitext(f)[1].lower() in ['.xlsm', '.xlam', '.dotm', '.docm']:
                        all_files.append(os.path.join(candidate, f))

        if all_files:
            print(f"Found {len(all_files)} template file(s):")
            for f in all_files:
                print(f"  {f}")
            print()

            # Use current directory as output
            output_dir = os.getcwd()
            print(f"Output directory: {output_dir}")
            print()

            results = process_directory(os.path.dirname(all_files[0]), output_dir)
        else:
            print("No template files found in common directories.")
            print()
            print("Usage:")
            print(f"  python {sys.argv[0]} <template_file> [output_directory]")
            print()
            print("Examples:")
            print(f"  python {sys.argv[0]} template.xlam")
            print(f"  python {sys.argv[0]} template.dotm D:\\output")
            return
    else:
        # Command line mode
        template_path = sys.argv[1]

        if len(sys.argv) >= 3:
            output_dir = sys.argv[2]
        else:
            output_dir = os.path.dirname(template_path) or os.getcwd()

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        if os.path.isdir(template_path):
            # Process directory
            results = process_directory(template_path, output_dir)
        else:
            # Process single file
            results = {'success': 0, 'failed': 0, 'total': 1}
            if extract_vba_project(template_path, output_dir):
                results['success'] = 1
            else:
                results['failed'] = 1

    # Print summary
    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    if 'total' in results:
        print(f"Total: {results['total']}, Success: {results['success']}, Failed: {results['failed']}")

    if results.get('success', 0) > 0:
        print()
        print("Next steps:")
        print("1. Copy the extracted vbaProject.bin files to your deployment system")
        print("2. Rename them to:")
        print("   - vbaProject_excel.bin (for Excel templates)")
        print("   - vbaProject_word.bin (for Word templates)")
        print("3. Place them in the templates directory:")
        print("   D:\\ScriptNexus\\templates\\")
    print("=" * 60)


if __name__ == '__main__':
    main()
