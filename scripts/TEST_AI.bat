@echo off
cd /d "%~dp0"
echo ==========================================
echo      JoJo Trader - AI Connection Test
echo ==========================================
echo.
echo Running diagnostics with virtual environment...
echo.

".venv\Scripts\python.exe" test_ai.py

echo.
echo ==========================================
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Test script failed with error code %ERRORLEVEL%.
    echo Please check the error message above.
)
echo.
pause
