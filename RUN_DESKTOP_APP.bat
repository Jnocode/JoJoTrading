@echo off
echo ===================================================
echo   Starting JoJo Trading Desktop App (PySide6)
echo ===================================================
cd /d "%~dp0"

cd desktop_app
:: Use direct path for robustness
"..\.venv\Scripts\python.exe" real_desktop_app.py

if %errorlevel% neq 0 (
    echo.
    echo ❌ Application exited with error code %errorlevel%
    echo.
)
cd ..

pause
