#!/usr/bin/env python
"""Deployment packaging script for ScriptNexus project.

Creates a minimal deployment package by excluding:
- __pycache__ directories
- .pyc files
- .git directory
- .pytest_cache
- Database files (*.db)
- Log files (*.log)
- Test files (optional)
- Build artifacts

Usage:
    python package_deploy.py [--output OUTPUT.zip] [--no-tests]
"""

import os
import sys
import zipfile
import argparse
from datetime import datetime
from pathlib import Path

# Directories to exclude
EXCLUDE_DIRS = {
    '__pycache__',
    '.git',
    '.pytest_cache',
    '.idea',
    '.vscode',
    'venv',
    '.venv',
    'env',
    '.env',
    'node_modules',
    'build',
    'dist',
    '.eggs',
    '*.egg-info',
}

# File patterns to exclude
EXCLUDE_FILES = {
    '*.pyc',
    '*.pyo',
    '*.pyd',
    '*.db',
    '*.log',
    '*.bak',
    '.DS_Store',
    'Thumbs.db',
    '*.orig',
    '*~',
}

# Optional: exclude test files for smaller package
EXCLUDE_TEST_DIRS = {'tests', 'test'}


def should_exclude_dir(dir_name: str, dir_path: Path) -> bool:
    """Check if directory should be excluded."""
    # Check exact name match
    if dir_name in EXCLUDE_DIRS:
        return True

    # Check pattern match (e.g., *.egg-info)
    for pattern in EXCLUDE_DIRS:
        if pattern.startswith('*') and dir_name.endswith(pattern[1:]):
            return True

    return False


def should_exclude_file(file_name: str) -> bool:
    """Check if file should be excluded."""
    for pattern in EXCLUDE_FILES:
        if pattern.startswith('*') and file_name.endswith(pattern[1:]):
            return True
    return False


def should_exclude_test_dir(dir_path: Path, root: Path) -> bool:
    """Check if directory is a test directory."""
    rel_path = dir_path.relative_to(root)
    parts = rel_path.parts
    return any(part in EXCLUDE_TEST_DIRS for part in parts)


def get_files_to_package(root: Path, exclude_tests: bool = False) -> list:
    """Get list of files to include in package."""
    files = []

    for dirpath, dirnames, filenames in os.walk(root):
        # Skip hidden directories
        dirnames[:] = [d for d in dirnames if not d.startswith('.')]

        current_dir = Path(dirpath)

        # Remove excluded directories from traversal
        dirnames[:] = [
            d for d in dirnames
            if not should_exclude_dir(d, current_dir)
        ]

        # Optionally exclude test directories
        if exclude_tests:
            dirnames[:] = [
                d for d in dirnames
                if not should_exclude_test_dir(current_dir / d, root)
            ]

        # Add files
        for filename in filenames:
            if not filename.startswith('.') and not should_exclude_file(filename):
                file_path = current_dir / filename
                files.append(file_path)

    return files


def create_package(root: Path, output: Path, exclude_tests: bool = False) -> dict:
    """Create deployment package."""
    files = get_files_to_package(root, exclude_tests)

    stats = {
        'total_files': len(files),
        'total_size': 0,
        'compressed_size': 0,
    }

    print(f"Creating deployment package: {output}")
    print(f"Files to package: {stats['total_files']}")
    print()

    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file_path in files:
            # Calculate relative path for archive
            arcname = file_path.relative_to(root)

            # Add file to archive
            zf.write(file_path, arcname)

            # Update stats
            try:
                file_info = zf.getinfo(str(arcname))
                stats['total_size'] += file_info.file_size
                stats['compressed_size'] += file_info.compress_size
            except:
                pass

    return stats


def print_summary(stats: dict, output: Path, duration: float):
    """Print packaging summary."""
    print()
    print("=" * 60)
    print("Packaging Complete!")
    print("=" * 60)
    print(f"Output file: {output}")
    print(f"Total files: {stats['total_files']}")
    print(f"Original size: {stats['total_size'] / 1024:.1f} KB")
    print(f"Compressed size: {stats['compressed_size'] / 1024:.1f} KB")
    print(f"Compression ratio: {100 - (stats['compressed_size'] / max(stats['total_size'], 1) * 100):.1f}%")
    print(f"Duration: {duration:.2f} seconds")
    print()
    print("Transfer this file to the internal network:")
    print(f"  {output}")
    print()
    print("On the internal network, extract with:")
    print(f"  unzip {output.name} -d ScriptNexus/")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description='Create deployment package for ScriptNexus')
    parser.add_argument('--root', '-r', default='.', help='Project root directory (default: current directory)')
    parser.add_argument('--output', '-o', default=None, help='Output ZIP file path')
    parser.add_argument('--no-tests', action='store_true', help='Exclude test files')
    parser.add_argument('--list-files', '-l', action='store_true', help='List files to be packaged without creating archive')

    args = parser.parse_args()

    root = Path(args.root).resolve()

    if not root.exists():
        print(f"Error: Root directory does not exist: {root}")
        sys.exit(1)

    # Generate output filename if not specified
    if args.output:
        output = Path(args.output).resolve()
    else:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        tests_suffix = '_no_tests' if args.no_tests else ''
        output = root / f'ScriptNexus_deploy_{timestamp}{tests_suffix}.zip'

    if args.list_files:
        # Just list files
        print("Files to be packaged:")
        print("-" * 60)
        files = get_files_to_package(root, args.no_tests)
        for f in sorted(files):
            print(f"  {f.relative_to(root)}")
        print("-" * 60)
        print(f"Total: {len(files)} files")
        return

    # Create package
    import time
    start = time.time()
    stats = create_package(root, output, args.no_tests)
    duration = time.time() - start

    print_summary(stats, output, duration)


if __name__ == '__main__':
    main()
