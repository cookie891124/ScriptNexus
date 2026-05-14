#!/usr/bin/env python
"""Incremental deployment packaging script for ScriptNexus project.

Creates an incremental package containing only files that have changed
since the last package was created.

Usage:
    # First time: create full package
    python package_incremental.py --init

    # Subsequent: create incremental package
    python package_incremental.py

    # Apply incremental package on internal network
    python package_incremental.py --apply increment_20260415_120000.zip
"""

import os
import sys
import json
import zipfile
import hashlib
import argparse
import shutil
from datetime import datetime
from pathlib import Path

# State file to track last package state
STATE_FILE = Path('.deploy_state.json')

# Import exclude patterns from package_deploy.py
EXCLUDE_DIRS = {
    '__pycache__',
    '.git',
    '.pytest_cache',
    '.idea',
    '.vscode',
    'venv',
    '.venv',
}

EXCLUDE_FILES = {
    '*.pyc',
    '*.db',
    '*.log',
    '*.bak',
    '.DS_Store',
}

EXCLUDE_TEST_DIRS = {'tests', 'test'}


def load_state() -> dict:
    """Load previous deployment state."""
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'files': {}, 'last_package': None}


def save_state(state: dict):
    """Save deployment state."""
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def get_file_hash(file_path: Path) -> str:
    """Calculate MD5 hash of a file."""
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hasher.update(chunk)
    return hasher.hexdigest()


def should_exclude_dir(dir_name: str, dir_path: Path) -> bool:
    if dir_name in EXCLUDE_DIRS:
        return True
    for pattern in EXCLUDE_DIRS:
        if pattern.startswith('*') and dir_name.endswith(pattern[1:]):
            return True
    return False


def should_exclude_file(file_name: str) -> bool:
    for pattern in EXCLUDE_FILES:
        if pattern.startswith('*') and file_name.endswith(pattern[1:]):
            return True
    return False


def should_exclude_test_dir(dir_path: Path, root: Path) -> bool:
    rel_path = dir_path.relative_to(root)
    parts = rel_path.parts
    return any(part in EXCLUDE_TEST_DIRS for part in parts)


def scan_files(root: Path, exclude_tests: bool = True) -> dict:
    """Scan directory and return file hashes."""
    files = {}

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith('.')]
        current_dir = Path(dirpath)

        dirnames[:] = [d for d in dirnames if not should_exclude_dir(d, current_dir)]

        if exclude_tests:
            dirnames[:] = [d for d in dirnames if not should_exclude_test_dir(current_dir / d, root)]

        for filename in filenames:
            if not filename.startswith('.') and not should_exclude_file(filename):
                file_path = current_dir / filename
                rel_path = str(file_path.relative_to(root))

                # Skip state file and output packages
                if rel_path == str(STATE_FILE) or rel_path.endswith('.zip'):
                    continue

                files[rel_path] = get_file_hash(file_path)

    return files


def create_incremental_package(root: Path, output: Path) -> dict:
    """Create incremental package with changed files only."""
    state = load_state()
    old_files = state.get('files', {})

    # Scan current files
    current_files = scan_files(root)

    # Find changes
    changes = {
        'added': [],
        'modified': [],
        'deleted': [],
        'unchanged': [],
    }

    # Check for added and modified files
    for rel_path, new_hash in current_files.items():
        if rel_path not in old_files:
            changes['added'].append(rel_path)
        elif old_files[rel_path] != new_hash:
            changes['modified'].append(rel_path)
        else:
            changes['unchanged'].append(rel_path)

    # Check for deleted files
    for rel_path in old_files:
        if rel_path not in current_files:
            changes['deleted'].append(rel_path)

    stats = {
        'added': len(changes['added']),
        'modified': len(changes['modified']),
        'deleted': len(changes['deleted']),
        'unchanged': len(changes['unchanged']),
        'total_files': len(current_files),
    }

    print(f"Creating incremental package: {output}")
    print(f"  Added:    {stats['added']} files")
    print(f"  Modified: {stats['modified']} files")
    print(f"  Deleted:  {stats['deleted']} files (metadata only)")
    print(f"  Unchanged: {stats['unchanged']} files (not included)")
    print()

    # Create package
    files_to_package = changes['added'] + changes['modified']

    if not files_to_package:
        print("No files changed. Skipping package creation.")
        return {'skip': True, 'changes': changes}

    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add change metadata
        zf.writestr('CHANGE_MANIFEST.json', json.dumps({
            'type': 'incremental',
            'timestamp': datetime.now().isoformat(),
            'changes': changes,
        }, indent=2, ensure_ascii=False))

        # Add changed files
        for rel_path in files_to_package:
            file_path = root / rel_path
            zf.write(file_path, rel_path)

    # Update state
    state['files'] = current_files
    state['last_package'] = str(output)
    state['last_package_time'] = datetime.now().isoformat()
    save_state(state)

    return {'skip': False, 'changes': changes, 'stats': stats}


def apply_incremental_package(package_path: Path, target_dir: Path) -> bool:
    """Apply incremental package to target directory."""
    if not package_path.exists():
        print(f"Error: Package not found: {package_path}")
        return False

    print(f"Applying incremental package: {package_path}")
    print(f"Target directory: {target_dir}")
    print()

    with zipfile.ZipFile(package_path, 'r') as zf:
        # Check if it's an incremental package
        if 'CHANGE_MANIFEST.json' not in zf.namelist():
            print("Error: Not a valid incremental package (missing CHANGE_MANIFEST.json)")
            return False

        # Read manifest
        manifest = json.loads(zf.read('CHANGE_MANIFEST.json'))
        changes = manifest.get('changes', {})

        # Apply file updates
        for rel_path in changes.get('added', []) + changes.get('modified', []):
            file_path = target_dir / rel_path

            # Create parent directories
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Extract file
            zf.extract(rel_path, target_dir)
            print(f"  Updated: {rel_path}")

        # Handle deletions
        for rel_path in changes.get('deleted', []):
            file_path = target_dir / rel_path
            if file_path.exists():
                file_path.unlink()
                print(f"  Deleted: {rel_path}")

    print()
    print("Incremental update applied successfully!")
    return True


def create_full_package(root: Path, output: Path) -> dict:
    """Create full deployment package."""
    from package_deploy import get_files_to_package, create_package, print_summary
    import time

    start = time.time()
    stats = create_package(root, output, exclude_tests=True)
    duration = time.time() - start

    # Update state
    state = {
        'files': scan_files(root),
        'last_package': str(output),
        'last_package_time': datetime.now().isoformat(),
        'type': 'full',
    }
    save_state(state)

    print_summary(stats, output, duration)
    return stats


def main():
    parser = argparse.ArgumentParser(description='Incremental deployment packaging')
    parser.add_argument('--root', '-r', default='.', help='Project root directory')
    parser.add_argument('--output', '-o', default=None, help='Output ZIP file path')
    parser.add_argument('--init', action='store_true', help='Create full initial package')
    parser.add_argument('--apply', metavar='PACKAGE', help='Apply incremental package to target')
    parser.add_argument('--target', '-t', default='.', help='Target directory for --apply')
    parser.add_argument('--show-state', action='store_true', help='Show current deployment state')

    args = parser.parse_args()
    root = Path(args.root).resolve()

    if args.show_state:
        state = load_state()
        print("Current deployment state:")
        print(f"  Last package: {state.get('last_package', 'None')}")
        print(f"  Last update: {state.get('last_package_time', 'Never')}")
        print(f"  Type: {state.get('type', 'unknown')}")
        print(f"  Tracked files: {len(state.get('files', {}))}")
        return

    if args.apply:
        target = Path(args.target).resolve()
        success = apply_incremental_package(Path(args.apply), target)
        sys.exit(0 if success else 1)

    output = Path(args.output) if args.output else None

    if args.init:
        print("Creating FULL deployment package...")
        print()
        if output is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output = root / f'ScriptNexus_full_{timestamp}.zip'
        create_full_package(root, output)
    else:
        print("Creating INCREMENTAL deployment package...")
        print()
        if output is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output = root / f'ScriptNexus_increment_{timestamp}.zip'

        result = create_incremental_package(root, output)

        if result.get('skip'):
            print("\nNo changes detected. No package created.")
            return

        stats = result.get('stats', {})
        print()
        print("=" * 60)
        print("Incremental Package Created!")
        print("=" * 60)
        print(f"Output: {output}")
        print(f"Changed files: {stats.get('added', 0) + stats.get('modified', 0)}")
        print()
        print("On internal network, apply with:")
        print(f"  python package_incremental.py --apply {output.name} --target /path/to/ScriptNexus")
        print("=" * 60)


if __name__ == '__main__':
    main()
