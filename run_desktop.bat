@echo off
setlocal
echo Starting JoJo Trader Desktop...

:: 1. Try to find python
python --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=python
    goto :FOUND
)

py --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=py
    goto :FOUND
)

echo [ERROR] Python not found in PATH. Please install Python.
goto :END

:FOUND
echo Found Python: %PYTHON_CMD%
echo Checking dependencies...
"%PYTHON_CMD%" scripts/check_dependencies.py
if %errorlevel% neq 0 (
    echo [WARNING] Dependency check failed.
)

echo Launching App...
%PYTHON_CMD% src/jojo_trader/main_desktop.py

:END
pause
