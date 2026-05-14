@echo off
chcp 65001 >nul
cd /d %~dp0

echo ============================================================
echo    ScriptNexus Windows EXE Build Script
echo ============================================================
echo.

REM Check PyInstaller
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
    echo.
)

REM Check if icons exist
if not exist pics\icon.ico (
    echo Generating icons...
    python tools\generate_icons.py
    echo.
)

REM Clean previous build
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Build executable
echo Building executable...
echo.
pyinstaller --clean --noconfirm scriptnexus.spec

if exist dist\ScriptNexus.exe (
    echo.
    echo ============================================================
    echo    Build successful!
    echo ============================================================
    echo.
    echo Output: dist\ScriptNexus.exe
    echo.

    REM Create distribution package
    echo Creating distribution package...
    if not exist dist\ScriptNexus-Package mkdir dist\ScriptNexus-Package
    copy dist\ScriptNexus.exe dist\ScriptNexus-Package\

    REM Copy templates
    if exist templates (
        xcopy templates dist\ScriptNexus-Package\templates\ /E /I /Y
    )

    REM Copy data (default config)
    if exist data (
        xcopy data dist\ScriptNexus-Package\data\ /E /I /Y
    )

    REM Copy pics (icons)
    if exist pics (
        xcopy pics dist\ScriptNexus-Package\pics\ /E /I /Y
    )

    echo.
    echo Distribution package ready: dist\ScriptNexus-Package\
    echo.

    REM Get file size
    for %%I in (dist\ScriptNexus.exe) do echo File size: %%~zI bytes

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