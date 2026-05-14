"""Dependency service for analyzing and managing Python script dependencies."""

import os
import re
import subprocess
from typing import List, Dict, Any, Optional


# Standard library modules for Python 3.10
STDLIB_MODULES = {
    'abc', 'aifc', 'argparse', 'array', 'ast', 'asynchat', 'asyncio',
    'asyncore', 'atexit', 'audioop', 'base64', 'bdb', 'binascii',
    'binhex', 'bisect', 'builtins', 'bz2', 'calendar', 'cgi', 'cgitb',
    'chunk', 'cmath', 'cmd', 'code', 'codecs', 'codeop', 'collections',
    'colorsys', 'compileall', 'concurrent', 'configparser', 'contextlib',
    'contextvars', 'copy', 'copyreg', 'cProfile', 'crypt', 'csv',
    'ctypes', 'curses', 'dataclasses', 'datetime', 'dbm', 'decimal',
    'difflib', 'dis', 'distutils', 'doctest', 'email', 'encodings',
    'enum', 'errno', 'faulthandler', 'fcntl', 'filecmp', 'fileinput',
    'fnmatch', 'fractions', 'ftplib', 'functools', 'gc', 'getopt',
    'getpass', 'gettext', 'glob', 'graphlib', 'grp', 'gzip', 'hashlib',
    'heapq', 'hmac', 'html', 'http', 'idlelib', 'imaplib', 'imghdr',
    'imp', 'importlib', 'inspect', 'io', 'ipaddress', 'itertools',
    'json', 'keyword', 'lib2to3', 'linecache', 'locale', 'logging',
    'lzma', 'mailbox', 'mailcap', 'marshal', 'math', 'mimetypes',
    'mmap', 'modulefinder', 'multiprocessing', 'netrc', 'nis',
    'nntplib', 'numbers', 'operator', 'optparse', 'os', 'ossaudiodev',
    'pathlib', 'pdb', 'pickle', 'pickletools', 'pipes', 'pkgutil',
    'platform', 'plistlib', 'poplib', 'posix', 'posixpath', 'pprint',
    'profile', 'pstats', 'pty', 'pwd', 'py_compile', 'pyclbr',
    'pydoc', 'queue', 'quopri', 'random', 're', 'readline', 'reprlib',
    'resource', 'rlcompleter', 'runpy', 'sched', 'secrets', 'select',
    'selectors', 'shelve', 'shlex', 'shutil', 'signal', 'site',
    'smtpd', 'smtplib', 'sndhdr', 'socket', 'socketserver', 'spwd',
    'sqlite3', 'ssl', 'stat', 'statistics', 'string', 'stringprep',
    'struct', 'subprocess', 'sunau', 'symtable', 'sys', 'sysconfig',
    'syslog', 'tabnanny', 'tarfile', 'telnetlib', 'tempfile', 'termios',
    'test', 'textwrap', 'threading', 'time', 'timeit', 'tkinter',
    'token', 'tokenize', 'trace', 'traceback', 'tracemalloc', 'tty',
    'turtle', 'turtledemo', 'types', 'typing', 'unicodedata', 'unittest',
    'urllib', 'uu', 'uuid', 'venv', 'warnings', 'wave', 'weakref',
    'webbrowser', 'winreg', 'winsound', 'wsgiref', 'xdrlib', 'xml',
    'xmlrpc', 'zipapp', 'zipfile', 'zipimport', 'zlib', '_thread',
    'typing_extensions', 'zoneinfo', 'tomllib', 'wsgiref', 'ensurepip'
}

# Mapping from import name to pip package name
# Some packages have different import names than their pip package names
IMPORT_TO_PACKAGE_MAP = {
    'appium': 'appium-python-client',
    'cv2': 'opencv-python',
    'PIL': 'pillow',
    'sklearn': 'scikit-learn',
    'yaml': 'pyyaml',
    'bs4': 'beautifulsoup4',
    'dateutil': 'python-dateutil',
    'dotenv': 'python-dotenv',
    'jwt': 'pyjwt',
    'serial': 'pyserial',
    'usb': 'pyusb',
    'wx': 'wxpython',
}


class DependencyService:
    """Service for analyzing and managing Python script dependencies."""

    def __init__(self, whl_dir: str):
        """Initialize the dependency service.

        Args:
            whl_dir: Path to the whl file pool directory.
        """
        self.whl_dir = whl_dir
        # Only create directory if path is valid and non-empty
        if whl_dir and not os.path.exists(whl_dir):
            os.makedirs(whl_dir)

        # Reference to PythonService for script retrieval
        self.python_service = None

    def set_python_service(self, python_service) -> None:
        """Set the PythonService reference for script retrieval.

        Args:
            python_service: PythonService instance.
        """
        self.python_service = python_service

    def get_script(self, script_id: int) -> Optional[Dict[str, Any]]:
        """Get a script by ID via PythonService.

        Args:
            script_id: The script ID.

        Returns:
            Script data as a dictionary, or None if not found.
        """
        if self.python_service:
            return self.python_service.get_script(script_id)
        return None

    def analyze_imports(self, code: str) -> List[str]:
        """Analyze import statements in code.

        Args:
            code: Python source code.

        Returns:
            List of imported module names.
        """
        imports = []

        # Pattern for: import module
        import_pattern = r'^\s*import\s+([\w\.]+)'
        # Pattern for: from module import ...
        from_pattern = r'^\s*from\s+([\w\.]+)\s+import'

        for line in code.split('\n'):
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue

            # Match "import X" or "import X as Y"
            match = re.match(import_pattern, line)
            if match:
                module = match.group(1).split('.')[0]  # Get root module
                if module not in imports:
                    imports.append(module)
                continue

            # Match "from X import Y"
            match = re.match(from_pattern, line)
            if match:
                module = match.group(1).split('.')[0]  # Get root module
                if module not in imports:
                    imports.append(module)

        return imports

    def _get_whl_packages(self) -> Dict[str, str]:
        """Get packages available in the whl file pool.

        Returns:
            Dictionary mapping package names to versions.
        """
        packages = {}

        if not os.path.exists(self.whl_dir):
            return packages

        for filename in os.listdir(self.whl_dir):
            if filename.endswith('.whl'):
                # Parse wheel filename: {distribution}-{version}(-{build tag})?-{python}-{abi}-{platform}.whl
                parts = filename.split('-')
                if len(parts) >= 2:
                    name = parts[0].lower()
                    version = parts[1]
                    packages[name] = version

        return packages

    def _find_whl(self, package_name: str) -> Optional[str]:
        """Find a whl file for the given package name.

        Args:
            package_name: Package name to search for.

        Returns:
            Path to the whl file, or None if not found.
        """
        if not os.path.exists(self.whl_dir):
            return None

        package_name = package_name.lower()

        for filename in os.listdir(self.whl_dir):
            if filename.endswith('.whl'):
                # Extract package name from filename
                parts = filename.split('-')
                if parts and parts[0].lower() == package_name:
                    return os.path.join(self.whl_dir, filename)

        return None

    def install_from_whl(self, package_name: str) -> Dict[str, Any]:
        """Install a package from the whl file pool.

        Args:
            package_name: Package name to install.

        Returns:
            Dictionary with success status and error message.
        """
        whl_path = self._find_whl(package_name)

        if whl_path is None:
            return {
                "success": False,
                "error": f"Package '{package_name}' not found in whl pool",
                "attempted": False
            }

        try:
            # Use pip to install from whl
            cmd = f'pip install "{whl_path}" --force-reinstall'
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                return {
                    "success": True,
                    "whl_path": whl_path,
                    "attempted": True
                }
            else:
                return {
                    "success": False,
                    "error": result.stderr or result.stdout,
                    "whl_path": whl_path,
                    "attempted": True
                }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Installation timed out",
                "whl_path": whl_path,
                "attempted": True
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "whl_path": whl_path,
                "attempted": True
            }

    def check_missing(self, script_id: int) -> List[str]:
        """Check for missing dependencies of a script.

        Args:
            script_id: The script ID.

        Returns:
            List of missing package names.
        """
        script = self.get_script(script_id)

        if script is None:
            return []

        code = script.get("code", "")
        imports = self.analyze_imports(code)
        whl_packages = self._get_whl_packages()
        installed_packages = self._get_installed_packages()

        missing = []

        for module in imports:
            module_lower = module.lower()

            # Skip stdlib modules
            if module_lower in STDLIB_MODULES:
                continue

            # Check if installed via pip (check both import name and mapped package name)
            if self._is_package_installed(module_lower, installed_packages):
                continue

            # Check if available in whl pool
            if module_lower not in whl_packages:
                missing.append(module)

        return missing

    def _is_package_installed(self, import_name: str, installed_packages: Dict[str, str]) -> bool:
        """Check if a package is installed by import name or mapped package name.

        Args:
            import_name: Import name used in code
            installed_packages: Dictionary of installed packages

        Returns:
            True if package is installed, False otherwise
        """
        import_name_lower = import_name.lower()

        # Direct match
        if import_name_lower in installed_packages:
            return True

        # Check if import name has a mapped package name
        if import_name_lower in IMPORT_TO_PACKAGE_MAP:
            mapped_package = IMPORT_TO_PACKAGE_MAP[import_name_lower]
            if mapped_package.lower() in installed_packages:
                return True

        # Reverse check: if any mapped import name matches
        for imp_name, pkg_name in IMPORT_TO_PACKAGE_MAP.items():
            if pkg_name.lower() == import_name_lower:
                if imp_name in installed_packages:
                    return True

        return False

    def _get_installed_packages(self, force_refresh: bool = False) -> Dict[str, str]:
        """Get packages installed in the current Python environment.

        Args:
            force_refresh: If True, bypass cache and refresh from pip.

        Returns:
            Dictionary mapping package names to versions.
        """
        # Check cache first (valid for 5 minutes)
        import time
        if not force_refresh and hasattr(self, '_packages_cache') and hasattr(self, '_packages_cache_time'):
            if time.time() - self._packages_cache_time < 300:
                return self._installed_packages

        packages = {}
        try:
            result = subprocess.run(
                ["pip", "list", "--format=freeze"],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if '==' in line:
                        name, version = line.split('==')
                        packages[name.lower()] = version
        except Exception:
            pass

        # Cache the result
        self._installed_packages = packages
        self._packages_cache_time = time.time()

        return packages
