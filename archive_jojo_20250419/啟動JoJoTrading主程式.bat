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
    set VENV_ACTIVATED=0
)

echo Starting JoJoTrading Quant System...

rem Try to activate venv and run python
if "%PYTHON_EXE%" NEQ "python" (
    echo Activating virtual environment: %PYTHON_EXE%
    call "%SCRIPT_DIR%venv\Scripts\activate.bat"
    if errorlevel 1 (
         echo [WARNING] Failed to activate venv using 'call'. Trying direct execution.
         "%PYTHON_EXE%" main.py
    ) else (
         echo Virtual environment activated. Running main.py...
         python main.py
         set VENV_ACTIVATED=1
    )
) else (
     echo No virtual environment found, using system python.
     "%PYTHON_EXE%" main.py
)

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to launch. Please check if Python or virtual environment exists.
    echo If you see "'python' is not recognized", please install Python or activate your virtual environment.
    echo Or manually edit this batch file to specify the correct python.exe path.
)
pause
