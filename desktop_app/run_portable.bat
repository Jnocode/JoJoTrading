@echo off
setlocal enabledelayedexpansion

REM ============================================================
REM JoJo Trader - Portable Desktop Launcher
REM ============================================================

REM Switch to the directory where this .bat lives
cd /d "%~dp0"

echo.
echo ============================================================
echo   JoJo Trader - Portable Desktop Launcher
echo ============================================================
echo.

REM ============================================================
REM Priority 1: Use sandboxed Embeddable Python
REM ============================================================
if exist "runtime_python\python.exe" (
    echo [OK] Portable Python environment detected.
    set "PYTHON_CMD=runtime_python\python.exe"
    goto LAUNCH
)

REM ============================================================
REM Sandbox not found - need to bootstrap the environment
REM Find any available Python to run portable_launcher.py
REM ============================================================
echo [INFO] First launch - deploying portable environment...
echo.

REM Try 1: Project-level .venv
if exist "..\.venv\Scripts\python.exe" (
    set "BOOTSTRAP_PY=..\.venv\Scripts\python.exe"
    goto SETUP
)

REM Try 2: System python
python --version >nul 2>&1
if !errorlevel! equ 0 (
    set "BOOTSTRAP_PY=python"
    goto SETUP
)

REM Try 3: Python Launcher
py --version >nul 2>&1
if !errorlevel! equ 0 (
    set "BOOTSTRAP_PY=py"
    goto SETUP
)

REM No Python found at all
echo.
echo ============================================================
echo   [ERROR] Python not found!
echo.
echo   First launch requires Python to bootstrap the environment.
echo   Please install Python 3.11+:
echo     https://www.python.org/downloads/
echo.
echo   After installing, re-run this script.
echo ============================================================
goto END

REM ============================================================
REM Run environment setup
REM ============================================================
:SETUP
echo [SETUP] Using %BOOTSTRAP_PY% to bootstrap environment...
echo.
"%BOOTSTRAP_PY%" portable_launcher.py --setup
if !errorlevel! neq 0 (
    echo.
    echo [ERROR] Environment setup failed! Check the messages above.
    goto END
)

REM Setup done - switch to sandboxed Python
if exist "runtime_python\python.exe" (
    set "PYTHON_CMD=runtime_python\python.exe"
) else (
    echo [ERROR] runtime_python\python.exe not found after setup.
    goto END
)

REM ============================================================
REM Launch Desktop App (with auto dependency repair)
REM ============================================================
:LAUNCH
echo [CHECK] Verifying dependencies...

REM Auto-repair: scan for missing packages and install them
REM This is fast when all packages are present (~2 sec)
set "PYTHONPATH=%~dp0trading_libs;%~dp0..\src"
set "PATH=%~dp0runtime_python;%~dp0runtime_python\Scripts;%PATH%"

"%PYTHON_CMD%" portable_launcher.py --deps-check
if !errorlevel! neq 0 (
    echo.
    echo [WARN] Some dependency issues found, but continuing...
)

echo [LAUNCH] Starting JoJo Trader Desktop...

"%PYTHON_CMD%" real_desktop_app.py
if !errorlevel! neq 0 (
    echo.
    echo [ERROR] Desktop App exited abnormally.
    echo Try running: "%PYTHON_CMD%" portable_launcher.py --check
)

:END
echo.
pause
