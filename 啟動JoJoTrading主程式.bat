@echo off
rem Get script directory
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

rem Try to use virtual environment python if exists
if exist ".venv\Scripts\python.exe" (
    set PYTHON_EXE=.venv\Scripts\python.exe
) else if exist "venv\Scripts\python.exe" (
    set PYTHON_EXE=venv\Scripts\python.exe
) else (
    set PYTHON_EXE=python
)

echo Starting JoJoTrading Quant System...
"%PYTHON_EXE%" gui.py
if errorlevel 1 (
    echo.
    echo [ERROR] Failed to launch. Please check if Python or virtual environment exists.
    echo If you see "'python' is not recognized", please install Python or activate your virtual environment.
    echo Or manually edit this batch file to specify the correct python.exe path.
)
pause
