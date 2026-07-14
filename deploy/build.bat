@echo off
:: Ensure we are in the project root directory
cd /d "%~dp0\.."

echo ==================================================
echo   Building Unilab Diagnostic System Executable
echo ==================================================
echo.

echo [1/3] Installing/verifying dependencies...
call .venv\Scripts\activate.bat
pip install Flask==3.0.0 mysql-connector-python==8.2.0 python-dotenv==1.0.0 werkzeug==3.0.1 waitress pyinstaller

echo.
echo [2/3] Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist UnilabSystem.spec del UnilabSystem.spec

echo.
echo [3/3] Running PyInstaller...
:: Build Main System
pyinstaller --name "UnilabSystem" --onefile --collect-all mysql.connector --add-data "static;static" --add-data "templates;templates" run.py

:: Build Backup System (silent console)
pyinstaller --name "backup_db" --onefile --noconsole --collect-all mysql.connector scripts\backup_db.py

echo.
echo ==================================================
echo   BUILD COMPLETE!
echo ==================================================
echo Executables generated:
echo 1. dist\UnilabSystem.exe
echo 2. dist\backup_db.exe
echo.
pause
