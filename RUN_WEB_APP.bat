@echo off
echo ===================================================
echo   Starting JoJo Trading Web App (Streamlit)
echo ===================================================
cd /d "%~dp0"

:: Use the venv python directly
".venv\Scripts\python.exe" web_app\app.py

if %errorlevel% neq 0 (
    echo.
    echo ❌ Application exited with error code %errorlevel%
    echo.
)

pause
