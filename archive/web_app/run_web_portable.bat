@echo off
setlocal enabledelayedexpansion

REM ============================================================
REM JoJo Trader Web App - Portable Launcher
REM ============================================================

REM Switch to the directory where this .bat lives
cd /d "%~dp0"

echo.
echo ============================================================
echo   JoJo Trader Web App - Portable Launcher
echo ============================================================
echo.

set "PYTHON_CMD=desktop_app\runtime_python\python.exe"
set "LIBS_DIR=desktop_app\trading_libs"

if not exist "%PYTHON_CMD%" (
    echo [ERROR] Portable Python environment not found!
    echo Please run "desktop_app\run_portable.bat" at least once to bootstrap the environment.
    echo After the environment is downloaded and setup, you can run this Web App launcher.
    echo.
    pause
    exit /b 1
)

echo [LAUNCH] Starting JoJo Trader Web App ^(Streamlit^)...

REM Setup PYTHONPATH so it finds the dependencies installed in trading_libs
set "PYTHONPATH=%~dp0%LIBS_DIR%;%~dp0src"

REM Include runtime_python in PATH just in case DLLs are needed
set "PATH=%~dp0desktop_app\runtime_python;%~dp0desktop_app\runtime_python\Scripts;%PATH%"

"%PYTHON_CMD%" -m streamlit run src\jojo_trading\ui\app.py

if !errorlevel! neq 0 (
    echo.
    echo [ERROR] Web App exited abnormally.
    echo Try running "desktop_app\run_portable.bat" to ensure all dependencies are installed.
)

echo.
pause
