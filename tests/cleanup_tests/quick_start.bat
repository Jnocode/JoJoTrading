@echo off
REM JoJo Trading Platform Quick Start Script

echo JoJo Trading Quick Start
echo ========================

cd /d "%~dp0"

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not installed
    pause
    exit /b 1
)

if exist "src\jojo_trading\ui\app.py" (
    set "MAIN_APP=src\jojo_trading\ui\app.py"
    echo Using refactored version
) else if exist "main_app.py" (
    set "MAIN_APP=main_app.py"
    echo Using standard version
) else if exist "main.py" (
    set "MAIN_APP=main.py"
    echo Using basic version
) else if exist "app.py" (
    set "MAIN_APP=app.py"
    echo Using basic version
) else (
    echo ERROR: No application found
    pause
    exit /b 1
)

echo Starting: %MAIN_APP%
echo Access at: http://localhost:8501
echo Press Ctrl+C to stop
echo.

streamlit run "%MAIN_APP%" --server.headless true

if %errorlevel% neq 0 (
    echo ERROR: Failed to start application
    pause
    exit /b 1
)

echo.
echo Application stopped.
pause
pause
