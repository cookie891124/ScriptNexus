@echo off
chcp 65001 >nul
REM increment.bat - Create incremental deployment package
REM Usage: Double-click or run .\increment.bat

cd /d %~dp0
echo ============================================================
echo ScriptNexus Incremental Packaging
echo ============================================================
echo.

REM Check if state file exists
if not exist .deploy_state.json (
    echo No deployment state found. Creating initial full package...
    echo.
    python tools/package_incremental.py --init
) else (
    echo Creating incremental package...
    echo.
    python tools/package_incremental.py
)

echo.
echo Package created! Transfer the .zip file to the internal network.
echo.
pause
