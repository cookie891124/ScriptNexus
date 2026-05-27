@echo off
chcp 65001 >nul
cd /d %~dp0

echo ============================================================
echo    ScriptNexus Kylin Linux Build Script (via Docker)
echo ============================================================
echo.
echo Target: Kylin Linux (x86_64)
echo Build Host: Windows
echo.

REM Check Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker not found. Please install Docker Desktop first.
    echo   Download: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)
echo Docker: OK
echo.

REM Select architecture
set ARCH=x86_64
if "%1"=="arm64" set ARCH=arm64
if "%1"=="aarch64" set ARCH=arm64
echo Target architecture: %ARCH%
echo.

REM Update spec file for architecture
echo Updating spec file for %ARCH%...
powershell -Command "(Get-Content scriptnexus-linux.spec) -replace 'target_arch=''[^'']*''', 'target_arch=''%ARCH%''' | Set-Content scriptnexus-linux.spec"
echo.

REM Clean previous build
echo Cleaning previous build...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
echo.

REM Generate icons if needed
if not exist pics\icon.png (
    echo Generating icons...
    python tools\generate_icons.py
    echo.
)

echo ============================================================
echo    Building in Docker container...
echo ============================================================
echo.

docker run --rm ^
    -v "%cd%:/app" ^
    -w /app ^
    ubuntu:22.04 ^
    bash -c "
        set -e;
        echo 'Updating apt...';
        apt-get update -qq;
        echo 'Installing Python...';
        apt-get install -y -qq python3 python3-pip python3-venv > /dev/null 2>&1;
        echo 'Installing PyInstaller...';
        pip3 install --quiet pyinstaller;
        echo 'Installing project dependencies...';
        pip3 install --quiet PyQt6 python-docx openpyxl;
        echo 'Building...';
        pyinstaller --clean --noconfirm scriptnexus-linux.spec;
        echo 'Done.';
    "

if exist dist\ScriptNexus (
    echo.
    echo ============================================================
    echo    Build successful!
    echo ============================================================
    echo.
    echo Output: dist\ScriptNexus\

    REM Create tar.gz for distribution
    echo Creating distribution archive...
    powershell -Command "tar -czf dist\ScriptNexus-Kylin-x86_64.tar.gz -C dist ScriptNexus"
    echo   dist\ScriptNexus-Kylin-x86_64.tar.gz
    echo.
    echo Deployment steps on Kylin:
    echo   1. Copy ScriptNexus-Kylin-x86_64.tar.gz to Kylin machine
    echo   2. tar -xzf ScriptNexus-Kylin-x86_64.tar.gz -C ~/
    echo   3. sudo apt install libxcb-cursor0
    echo   4. chmod +x ~/ScriptNexus/ScriptNexus
    echo   5. ~/ScriptNexus/ScriptNexus
    echo.

) else (
    echo.
    echo ============================================================
    echo    Build failed!
    echo ============================================================
    echo.
    echo Check the error messages above.
)

echo.
pause
