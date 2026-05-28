#!/bin/bash
# ============================================================
#    ScriptNexus Kylin Linux Build Script
# ============================================================
# Run this script ON the Kylin machine to build the executable.
#
# Usage:
#   chmod +x build_kylin.sh
#   ./build_kylin.sh              # x86_64 (most enterprise Kylin)
#   ./build_kylin.sh arm64        # ARM64 (Feiteng/Kirin chips)
# ============================================================

set -e

ARCH="${1:-x86_64}"

echo "============================================================"
echo "   ScriptNexus Kylin Linux Build"
echo "============================================================"
echo ""
echo "Target architecture: $ARCH"
echo ""

# ---- Check Python ----
if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 not found. Install it first:"
    echo "  sudo apt update && sudo apt install -y python3 python3-pip python3-venv"
    exit 1
fi

PYTHON_VER=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python: $PYTHON_VER"

PYTHON_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
PYTHON_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')

if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]; }; then
    echo "ERROR: Python 3.8+ required, found $PYTHON_VER"
    exit 1
fi

# ---- Install system deps ----
echo ""
echo "[1/5] Checking system dependencies..."

MISSING_PKGS=""
for pkg in libxcb-cursor0 libgl1 libegl1; do
    if ! dpkg -s "$pkg" &>/dev/null; then
        MISSING_PKGS="$MISSING_PKGS $pkg"
    fi
done

if [ -n "$MISSING_PKGS" ]; then
    echo "Installing system packages:$MISSING_PKGS"
    sudo apt update -qq
    sudo apt install -y $MISSING_PKGS
else
    echo "System dependencies: OK"
fi

# ---- Install Python deps ----
echo ""
echo "[2/5] Installing Python dependencies..."

if [ -f requirements.txt ]; then
    pip3 install --quiet -r requirements.txt
else
    pip3 install --quiet PyQt6 python-docx openpyxl
fi

echo "[3/5] Installing PyInstaller..."
pip3 install --quiet pyinstaller

# ---- Generate icons if needed ----
if [ ! -f pics/icon.png ]; then
    echo "[*] Generating icons..."
    python3 tools/generate_icons.py || true
fi

# ---- Update spec for architecture ----
echo ""
echo "[4/5] Configuring for $ARCH..."

if [ "$ARCH" = "arm64" ] || [ "$ARCH" = "aarch64" ]; then
    SPEC_ARCH="arm64"
else
    SPEC_ARCH="x86_64"
fi

sed -i "s/target_arch='[^']*'/target_arch='$SPEC_ARCH'/" scriptnexus-linux.spec

# ---- Build ----
echo ""
echo "[5/5] Building executable..."
rm -rf build dist

pyinstaller --clean --noconfirm scriptnexus-linux.spec

# ---- Verify ----
if [ -f dist/ScriptNexus/ScriptNexus ]; then
    echo ""
    echo "============================================================"
    echo "   Build successful!"
    echo "============================================================"
    echo ""
    echo "Output: dist/ScriptNexus/"
    echo "Executable: dist/ScriptNexus/ScriptNexus"
    echo ""

    # Make executable
    chmod +x dist/ScriptNexus/ScriptNexus

    # Create tar.gz for distribution
    ARCH_NAME=$(uname -m)
    TARBALL="ScriptNexus-Kylin-${ARCH_NAME}.tar.gz"
    echo "Creating distribution archive: $TARBALL"
    cd dist && tar -czf "$TARBALL" ScriptNexus && cd ..

    echo ""
    echo "To run on any Kylin machine:"
    echo "  1. Copy $TARBALL to target machine"
    echo "  2. tar -xzf $TARBALL -C ~/"
    echo "  3. sudo apt install -y libxcb-cursor0 libgl1 libegl1"
    echo "  4. ~/ScriptNexus/ScriptNexus"
    echo ""

else
    echo ""
    echo "============================================================"
    echo "   Build failed!"
    echo "============================================================"
    echo ""
    echo "Check the error messages above."
    exit 1
fi
