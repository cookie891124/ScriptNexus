@echo off
chcp 65001 >nul
cd /d %~dp0

echo ============================================================
echo    ScriptNexus Windows EXE Build Script
echo ============================================================
echo.

set PYTHON=C:\Users\L\AppData\Local\Programs\Python\Python310\python.exe

REM Check PyInstaller
%PYTHON% -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo Installing PyInstaller...
    %PYTHON% -m pip install pyinstaller
    echo.
)

REM Check if icons exist
if not exist pics\icon.ico (
    echo Generating icons...
    %PYTHON% tools\generate_icons.py
    echo.
)

REM Clean previous build
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Build executable
echo Building executable...
echo.
%PYTHON% -m PyInstaller --clean --noconfirm scriptnexus.spec

if exist dist\ScriptNexus.exe (
    echo.
    echo ============================================================
    echo    Build successful!
    echo ============================================================
    echo.
    echo Output: dist\ScriptNexus.exe

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
exit /b 0
