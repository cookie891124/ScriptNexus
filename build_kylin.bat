@echo off
chcp 65001 >nul
cd /d %~dp0

echo ============================================================
echo    ScriptNexus Kylin Linux Build — Source Package
echo ============================================================
echo.
echo This script packages the source for transfer to a Kylin machine.
echo Run build_kylin.sh on the Kylin machine to complete the build.
echo.

set PACKAGE_NAME=ScriptNexus-src.zip
set PACKAGE_DIR=ScriptNexus-src
set DEST=%cd%\dist

REM Clean and prepare
echo [1/4] Cleaning...
if exist "%DEST%\%PACKAGE_NAME%" del /q "%DEST%\%PACKAGE_NAME%"
if exist "%DEST%\%PACKAGE_DIR%" rmdir /s /q "%DEST%\%PACKAGE_DIR%"
if not exist "%DEST%" mkdir "%DIST%" 2>nul

echo [2/4] Copying source files...
robocopy "." "%DEST%\%PACKAGE_DIR%" ^
    app.py ^
    requirements.txt ^
    build_kylin.sh ^
    scriptnexus-linux.spec ^
    /NFL /NDL /NJH /NJS >nul 2>&1

robocopy "core" "%DEST%\%PACKAGE_DIR%\core" /E /XD __pycache__ /XF *.pyc /NFL /NDL /NJH /NJS >nul 2>&1
robocopy "models" "%DEST%\%PACKAGE_DIR%\models" /E /XD __pycache__ /XF *.pyc /NFL /NDL /NJH /NJS >nul 2>&1
robocopy "services" "%DEST%\%PACKAGE_DIR%\services" /E /XD __pycache__ /XF *.pyc /NFL /NDL /NJH /NJS >nul 2>&1
robocopy "ui" "%DEST%\%PACKAGE_DIR%\ui" /E /XD __pycache__ /XF *.pyc /NFL /NDL /NJH /NJS >nul 2>&1
robocopy "hooks" "%DEST%\%PACKAGE_DIR%\hooks" /E /XD __pycache__ /XF *.pyc /NFL /NDL /NJH /NJS >nul 2>&1
robocopy "data" "%DEST%\%PACKAGE_DIR%\data" config.example.json /NFL /NDL /NJH /NJS >nul 2>&1
robocopy "templates" "%DEST%\%PACKAGE_DIR%\templates" /E /NFL /NDL /NJH /NJS >nul 2>&1
robocopy "pics" "%DEST%\%PACKAGE_DIR%\pics" icon.png icon.svg /NFL /NDL /NJH /NJS >nul 2>&1
robocopy "scripts" "%DEST%\%PACKAGE_DIR%\scripts" /E /NFL /NDL /NJH /NJS >nul 2>&1
robocopy "tools" "%DEST%\%PACKAGE_DIR%\tools" generate_icons.py /NFL /NDL /NJH /NJS >nul 2>&1

REM Create empty required dirs
mkdir "%DEST%\%PACKAGE_DIR%\data" 2>nul
mkdir "%DEST%\%PACKAGE_DIR%\scripts" 2>nul

REM Copy config example as default
copy /y "data\config.example.json" "%DEST%\%PACKAGE_DIR%\data\config.json" >nul 2>&1

echo [3/4] Creating zip package...
powershell -Command "Compress-Archive -Path '%DEST%\%PACKAGE_DIR%' -DestinationPath '%DEST%\%PACKAGE_NAME%' -Force"

echo [4/4] Cleaning up temp dir...
rmdir /s /q "%DEST%\%PACKAGE_DIR%"

echo.
echo ============================================================
echo    Package created successfully!
echo ============================================================
echo.
echo Output: dist\%PACKAGE_NAME%
echo.
echo Next steps:
echo   1. Copy dist\%PACKAGE_NAME% to the Kylin machine
echo   2. On Kylin: unzip %PACKAGE_NAME% ^&^& cd %PACKAGE_DIR%
echo   3. On Kylin: chmod +x build_kylin.sh ^&^& ./build_kylin.sh
echo.
echo After the build completes on Kylin, the executable will be in:
echo   dist\ScriptNexus\ScriptNexus
echo.

pause
exit /b 0
