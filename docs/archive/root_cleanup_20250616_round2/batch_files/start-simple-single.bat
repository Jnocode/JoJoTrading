@echo off
chcp 65001 >nul 2>&1
title JoJo Trading v5.0.0 - Professional Edition
color 0A

echo.
echo ==========================================
echo    JoJo Trading v5.0.0 Professional
echo ==========================================
echo    AI 驅動投資分析平台
echo.

cd /d "%~dp0"

:: 檢查虛擬環境
echo [檢查] 檢查虛擬環境...
set "PYTHON_EXE="

if exist ".venv\Scripts\activate.bat" (
    echo [成功] 找到虛擬環境: .venv
    call .venv\Scripts\activate.bat
    set "PYTHON_EXE=.venv\Scripts\python.exe"
) else if exist "venv\Scripts\activate.bat" (
    echo [成功] 找到虛擬環境: venv
    call venv\Scripts\activate.bat
    set "PYTHON_EXE=venv\Scripts\python.exe"
) else if exist ".env\Scripts\activate.bat" (
    echo [成功] 找到虛擬環境: .env
    call .env\Scripts\activate.bat
    set "PYTHON_EXE=.env\Scripts\python.exe"
) else (
    echo [警告] 未找到虛擬環境，使用系統 Python
    set "PYTHON_EXE=python"
)

:: 檢查 Python 是否可用
%PYTHON_EXE% --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [錯誤] 找不到 Python
    echo        請確認已安裝 Python 3.8+ 或虛擬環境設定正確
    pause
    exit /b 1
)

echo [成功] Python 環境就緒
echo.
echo [啟動] JoJo Trading 主應用...
echo ==========================================
echo [提示] 完整功能導航，包含所有 Phase 5 功能
echo.

streamlit run streamlit_app.py

echo.
echo [完成] 感謝使用 JoJo Trading v5.0.0 Professional
pause
