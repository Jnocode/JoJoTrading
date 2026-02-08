@echo off
setlocal
echo ==========================================
echo       JoJo Trader - Settings Launcher
echo ==========================================

REM Defines paths
set "WORKSPACE_DIR=%~dp0"
set "VENV_PYTHON=%WORKSPACE_DIR%.venv\Scripts\python.exe"

REM Check for Virtual Environment
if exist "%VENV_PYTHON%" (
    echo [INFO] Found Virtual Environment at .venv
    set "PYTHON_CMD=%VENV_PYTHON%"
) else (
    echo [WARNING] .venv not found, attempting to use system 'python'...
    set "PYTHON_CMD=python"
)

REM Set PYTHONPATH to include src directory
set "PYTHONPATH=%WORKSPACE_DIR%src"
echo [INFO] PYTHONPATH set to: %PYTHONPATH%
echo [INFO] Using Python: %PYTHON_CMD%

REM Smart Dependency Check
"%PYTHON_CMD%" "%WORKSPACE_DIR%scripts\check_dependencies.py"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Dependency check failed.
    pause
    exit /b %ERRORLEVEL%
)

REM Execute
"%PYTHON_CMD%" "%WORKSPACE_DIR%src\jojo_trader\settings_app.py"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Application exited with error code: %ERRORLEVEL%
    pause
) else (
    echo [INFO] Application exited successfully.
)

endlocal
