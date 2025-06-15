@echo off
echo Starting JoJo Trading Platform...

cd /d "%~dp0"

echo Checking for virtual environment...
if exist ".venv\Scripts\activate.bat" (
    echo Found virtual environment: .venv
    call .venv\Scripts\activate.bat
    set "PYTHON_EXE=.venv\Scripts\python.exe"
) else if exist "venv\Scripts\activate.bat" (
    echo Found virtual environment: venv
    call venv\Scripts\activate.bat
    set "PYTHON_EXE=venv\Scripts\python.exe"
) else if exist ".env\Scripts\activate.bat" (
    echo Found virtual environment: .env
    call .env\Scripts\activate.bat
    set "PYTHON_EXE=.env\Scripts\python.exe"
) else (
    echo No virtual environment found, using system Python
    set "PYTHON_EXE=python"
)

%PYTHON_EXE% --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Please check your virtual environment or install Python 3.9+
    pause
    exit /b 1
)

%PYTHON_EXE% -c "import streamlit" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing Streamlit...
    %PYTHON_EXE% -m pip install streamlit
)

if exist "src\jojo_trading\ui\app.py" (
    set "MAIN_APP=src\jojo_trading\ui\app.py"
) else if exist "main_app.py" (
    set "MAIN_APP=main_app.py"
) else if exist "main.py" (
    set "MAIN_APP=main.py"
) else (
    echo ERROR: No application file found
    pause
    exit /b 1
)

echo Starting application: %MAIN_APP%
echo Access at: http://localhost:8501
echo.

REM Add src directory to Python path for module imports
set "PYTHONPATH=%CD%\src;%PYTHONPATH%"

%PYTHON_EXE% -m streamlit run "%MAIN_APP%"
