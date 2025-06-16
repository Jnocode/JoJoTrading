@echo off
chcp 65001 >nul 2>&1
title JoJo Trading v5.0.0 - Professional Edition
color 0A

echo.
echo ==========================================
echo    JoJo Trading v5.0.0 Professional
echo ==========================================
echo    Phase 5: 商業化與生態系統擴展
echo.

cd /d "%~dp0"

:: 檢查虛擬環境
echo [檢查] 檢查虛擬環境...
set "PYTHON_EXE="
set "VENV_FOUND=0"

if exist ".venv\Scripts\activate.bat" (
    echo [成功] 找到虛擬環境: .venv
    call .venv\Scripts\activate.bat
    set "PYTHON_EXE=.venv\Scripts\python.exe"
    set "VENV_FOUND=1"
) else if exist "venv\Scripts\activate.bat" (
    echo [成功] 找到虛擬環境: venv
    call venv\Scripts\activate.bat
    set "PYTHON_EXE=venv\Scripts\python.exe"
    set "VENV_FOUND=1"
) else if exist ".env\Scripts\activate.bat" (
    echo [成功] 找到虛擬環境: .env
    call .env\Scripts\activate.bat
    set "PYTHON_EXE=.env\Scripts\python.exe"
    set "VENV_FOUND=1"
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

:: 顯示主選單
:MENU
cls
echo.
echo ==========================================
echo    JoJo Trading v5.0.0 Professional
echo ==========================================
echo    AI 驅動投資分析平台
echo.
echo [選單] 請選擇啟動模式:
echo.
echo   1. [主應用] streamlit_app.py
echo   2. [用戶中心] 註冊/登入管理
echo   3. [導航系統] 智能功能導航
echo   4. [AI預測] 股價預測分析
echo   5. [DCF計算] 估值分析工具
echo   6. [Docker] 容器化啟動
echo   7. [Phase5] 商業化管理
echo   8. [系統狀態] 環境檢查
echo   9. [幫助信息] 使用指南
echo   0. [退出] 結束程式
echo.
echo ==========================================

set /p choice="請輸入選項 (0-9): "

echo.

if "%choice%"=="1" goto MAIN_APP
if "%choice%"=="2" goto USER_CENTER
if "%choice%"=="3" goto NAVIGATION
if "%choice%"=="4" goto AI_PREDICTOR
if "%choice%"=="5" goto DCF_CALCULATOR
if "%choice%"=="6" goto DOCKER_START
if "%choice%"=="7" goto PHASE5_MANAGER
if "%choice%"=="8" goto SYSTEM_STATUS
if "%choice%"=="9" goto HELP
if "%choice%"=="0" goto EXIT

echo [錯誤] 無效選項，請重新選擇
pause
goto MENU

:MAIN_APP
echo [啟動] 主應用 (streamlit_app.py)...
echo ==========================================
echo [提示] 這是 JoJo Trading 的主入口，包含完整功能導航
streamlit run streamlit_app.py
pause
goto MENU

:USER_CENTER
echo [啟動] 用戶中心...
echo ==========================================
echo [提示] 用戶註冊、登入、訂閱管理
:: 優先使用無 emoji 版本
if exist "pages\enhanced\00_User_Center.py" (
    streamlit run pages\enhanced\00_User_Center.py
) else (
    streamlit run "pages\enhanced\00_User_Center.py"
)
pause
goto MENU

:NAVIGATION
echo [啟動] 主導航系統...
echo ==========================================
echo [提示] 智能功能導航與快速入口
:: 優先使用無 emoji 版本
if exist "pages\enhanced\00_Navigation.py" (
    streamlit run pages\enhanced\00_Navigation.py
) else (
    streamlit run "pages\enhanced\00_Navigation.py"
)
pause
goto MENU

:AI_PREDICTOR
echo [啟動] AI 股價預測...
echo ==========================================
echo [提示] LSTM 深度學習股價預測 (需專業版)
:: 優先使用無 emoji 版本
if exist "pages\enhanced\advanced\08_AI_Stock_Predictor.py" (
    streamlit run pages\enhanced\advanced\08_AI_Stock_Predictor.py
) else (
    streamlit run "pages\enhanced\advanced\08_AI_Stock_Predictor.py"
)
pause
goto MENU

:DCF_CALCULATOR
echo [啟動] DCF 估值計算器...
echo ==========================================
echo [提示] 現金流折現估值分析
:: 優先使用無 emoji 版本
if exist "pages\enhanced\02_DCF_Calculator.py" (
    streamlit run pages\enhanced\02_DCF_Calculator.py
) else (
    streamlit run "pages\enhanced\02_DCF_Calculator.py"
)
pause
goto MENU

:DOCKER_START
echo [啟動] Docker 容器...
echo ==========================================
echo [提示] 檢查 Docker 狀態並啟動容器
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [錯誤] Docker 未安裝或未啟動
    echo [提示] 請先安裝 Docker Desktop
) else (
    echo [成功] Docker 可用，啟動容器...
    docker-compose up -d
    echo [完成] 容器啟動完成
)
pause
goto MENU

:PHASE5_MANAGER
echo [啟動] Phase 5 管理系統...
echo ==========================================
echo [提示] Phase 5 商業化與生態擴展管理
if exist "scripts\phase5_launch.py" (
    %PYTHON_EXE% scripts\phase5_launch.py --stage=all
) else (
    echo [警告] Phase 5 啟動腳本不存在
)
pause
goto MENU

:SYSTEM_STATUS
echo [檢查] 系統狀態檢查...
echo ==========================================
echo [Phase 4] 狀態: [完成] 100%% (企業級技術基礎)
echo [Phase 5] 狀態: [進行中] 商業化與生態擴展
echo.
echo [核心功能]
echo   [完成] 用戶管理系統 (註冊/登入/權限)
echo   [完成] AI 股價預測 (LSTM 深度學習)
echo   [完成] 三層訂閱方案 (免費/專業/企業)
echo   [完成] 統一導航系統
echo   [完成] Docker 容器化
echo.
echo [下週重點] AI 智能化升級與技術深化
echo.
echo [Python 版本]
%PYTHON_EXE% --version
echo.
echo [虛擬環境] 狀態: %VENV_FOUND%
echo.
echo [檔案結構檢查]
if exist "pages\enhanced\00_User_Center.py" (echo [成功] 用戶中心 (無emoji版)) else if exist "pages\enhanced\00_User_Center.py" (echo [成功] 用戶中心 (emoji版)) else (echo [錯誤] 用戶中心)
if exist "pages\enhanced\advanced\08_AI_Stock_Predictor.py" (echo [成功] AI預測 (無emoji版)) else if exist "pages\enhanced\advanced\08_AI_Stock_Predictor.py" (echo [成功] AI預測 (emoji版)) else (echo [錯誤] AI預測)
if exist "business\" (echo [成功] 商業化目錄) else (echo [錯誤] 商業化目錄)
if exist "api\" (echo [成功] API 目錄) else (echo [錯誤] API 目錄)
pause
goto MENU

:HELP
echo [幫助] 使用指南
echo ==========================================
echo [專案] JoJo Trading v5.0.0 Professional Edition
echo [描述] AI 驅動的專業投資分析平台
echo.
echo [使用指南]
echo   1. [主應用] 完整功能入口，推薦新用戶使用
echo   2. [用戶中心] 註冊帳號、選擇訂閱方案
echo   3. [導航系統] 智能功能導航系統
echo   4. [AI預測] LSTM 深度學習股價預測 (需專業版)
echo   5. [DCF計算] 現金流折現估值分析
echo   6. [Docker] 容器化部署 (需安裝 Docker)
echo   7. [Phase5] 商業化開發管理工具
echo   8. [系統狀態] 檢查專案完成度和環境
echo.
echo [訂閱方案]
echo   [免費版] 基礎 DCF 計算 (10次/月)
echo   [專業版] $29/月，無限 DCF + AI 分析
echo   [企業版] $99/月，完整 API + 白標方案
echo.
echo [技術支援]
echo   Email: support@jojo-trading.com
echo   文檔: https://docs.jojo-trading.com
echo   問題回報: https://github.com/jojo-trading/issues
pause
goto MENU

:EXIT
echo.
echo [再見] 感謝使用 JoJo Trading v5.0.0 Professional！
echo [目標] 打造世界級的 AI 投資分析平台
echo [狀態] Phase 5: 商業化與生態系統擴展成功啟動
echo.
pause
exit /b 0

:: 錯誤處理
:ERROR
echo.
echo [錯誤] 發生錯誤，請檢查設定
pause
goto MENU
