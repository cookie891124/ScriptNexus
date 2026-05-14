@echo off
chcp 65001 >nul
REM deploy.bat - Create full deployment package
REM Usage: Double-click or run .\deploy.bat

cd /d %~dp0
echo ============================================================
echo ScriptNexus Deployment Packaging
echo ============================================================
echo.

python tools/package_deploy.py --no-tests

echo.
echo Package created! Transfer the .zip file to the internal network.
echo.
pause
