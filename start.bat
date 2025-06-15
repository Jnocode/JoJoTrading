@echo off
title JoJo Trading Platform - 統一啟動器
color 0A

echo.
echo ==========================================
echo 🎯 JoJo Trading Platform 統一啟動器
echo ==========================================
echo.

cd /d "%~dp0"

:: 檢查虛擬環境
echo 🔍 檢查虛擬環境...
set "PYTHON_EXE="
set "VENV_FOUND=0"

if exist ".venv\Scripts\activate.bat" (
    echo ✅ 找到虛擬環境: .venv
    call .venv\Scripts\activate.bat
    set "PYTHON_EXE=.venv\Scripts\python.exe"
    set "VENV_FOUND=1"
) else if exist "venv\Scripts\activate.bat" (
    echo ✅ 找到虛擬環境: venv
    call venv\Scripts\activate.bat
    set "PYTHON_EXE=venv\Scripts\python.exe"
    set "VENV_FOUND=1"
) else if exist ".env\Scripts\activate.bat" (
    echo ✅ 找到虛擬環境: .env
    call .env\Scripts\activate.bat
    set "PYTHON_EXE=.env\Scripts\python.exe"
    set "VENV_FOUND=1"
) else (
    echo ⚠️  未找到虛擬環境，使用系統 Python
    set "PYTHON_EXE=python"
)

:: 檢查 Python 是否可用
%PYTHON_EXE% --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ❌ 錯誤: 找不到 Python
    echo    請確認已安裝 Python 3.8+ 或虛擬環境設定正確
    pause
    exit /b 1
)

echo ✅ Python 環境就緒
echo.

:: 顯示主選單
:MENU
cls
echo.
echo ==========================================
echo 🎯 JoJo Trading Platform 統一啟動器
echo ==========================================
echo.
echo 📋 請選擇啟動模式:
echo.
echo   1. 🚀 Web 應用 (推薦)
echo   2. ⚡ 快速啟動 (首次使用)
echo   3. 🎯 CLI 模式
echo   4. 🧪 系統測試
echo   5. 💡 簡化模式
echo   6. 📊 環境檢查
echo   7. ❓ 幫助信息
echo   8. 🚪 退出
echo.
echo ==========================================

set /p choice="請輸入選項 (1-8): "

echo.

if "%choice%"=="1" goto WEB_APP
if "%choice%"=="2" goto QUICK_START
if "%choice%"=="3" goto CLI_MODE
if "%choice%"=="4" goto SYSTEM_TEST
if "%choice%"=="5" goto SIMPLE_MODE
if "%choice%"=="6" goto ENV_CHECK
if "%choice%"=="7" goto HELP
if "%choice%"=="8" goto EXIT

echo ❌ 無效選項，請重新選擇
pause
goto MENU

:WEB_APP
echo 🚀 啟動 Web 應用...
echo ==========================================
%PYTHON_EXE% app.py
pause
goto MENU

:QUICK_START
echo ⚡ 快速啟動驗證...
echo ==========================================
%PYTHON_EXE% app.py --start
pause
goto MENU

:CLI_MODE
echo 🎯 啟動 CLI 模式...
echo ==========================================
%PYTHON_EXE% app.py --cli
pause
goto MENU

:SYSTEM_TEST
echo 🧪 執行系統測試...
echo ==========================================
%PYTHON_EXE% app.py --test
pause
goto MENU

:SIMPLE_MODE
echo 💡 啟動簡化模式...
echo ==========================================
%PYTHON_EXE% app.py --simple
pause
goto MENU

:ENV_CHECK
echo 📊 環境檢查...
echo ==========================================
%PYTHON_EXE% app.py --env-check
echo.
echo Python 版本:
%PYTHON_EXE% --version
echo.
echo 虛擬環境狀態: %VENV_FOUND%
pause
goto MENU

:HELP
echo ❓ 幫助信息
echo ==========================================
%PYTHON_EXE% app.py --help
pause
goto MENU

:EXIT
echo.
echo 👋 感謝使用 JoJo Trading Platform！
echo.
pause
exit /b 0

:: 錯誤處理
:ERROR
echo.
echo ❌ 發生錯誤，請檢查設定
pause
goto MENU
