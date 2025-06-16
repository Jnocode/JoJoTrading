@echo off
chcp 65001 >nul
title JoJo Trading v5.0.0 - Professional Edition
color 0A

echo.
echo ==========================================
echo  JoJo Trading v5.0.0 Professional
echo ==========================================
echo  Phase 5: 商業化與生態系統擴展
echo.

cd /d "%~dp0"

:: 檢查虛擬環境
echo 檢查 Python 環境...
set "PYTHON_EXE=python"

:: 檢查 Python 是否可用
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo 錯誤: 找不到 Python
    echo 請確認已安裝 Python 3.8+ 
    pause
    exit /b 1
)

echo Python 環境就緒
echo.

:: 主選單
:MENU
cls
echo.
echo ==========================================
echo  JoJo Trading v5.0.0 Professional
echo ==========================================
echo  AI 驅動投資分析平台
echo.
echo 請選擇啟動模式:
echo.
echo   1. 主應用 (streamlit_app.py)
echo   2. 用戶中心 (註冊/登入)
echo   3. 主導航系統
echo   4. AI 股價預測
echo   5. DCF 估值計算
echo   6. Docker 容器啟動
echo   7. Phase 5 管理
echo   8. 系統狀態
echo   9. 幫助信息
echo   0. 退出
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

echo 無效選項，請重新選擇
pause
goto MENU

:MAIN_APP
echo 啟動主應用...
echo ==========================================
echo 這是 JoJo Trading 的主入口，包含完整功能導航
python -m streamlit run streamlit_app.py
pause
goto MENU

:USER_CENTER
echo 啟動用戶中心...
echo ==========================================
echo 用戶註冊、登入、訂閱管理
python -m streamlit run pages/enhanced/00_User_Center.py
pause
goto MENU

:NAVIGATION
echo 啟動主導航系統...
echo ==========================================
echo 智能功能導航與快速入口
python -m streamlit run pages/enhanced/00_Navigation.py
pause
goto MENU

:AI_PREDICTOR
echo 啟動 AI 股價預測...
echo ==========================================
echo LSTM 深度學習股價預測 (需專業版)
python -m streamlit run pages/enhanced/advanced/08_AI_Stock_Predictor.py
pause
goto MENU

:DCF_CALCULATOR
echo 啟動 DCF 估值計算器...
echo ==========================================
echo 現金流折現估值分析
python -m streamlit run pages/enhanced/02_DCF_Calculator.py
pause
goto MENU

:DOCKER_START
echo 啟動 Docker 容器...
echo ==========================================
echo 檢查 Docker 狀態並啟動容器
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Docker 未安裝或未啟動
    echo 請先安裝 Docker Desktop
) else (
    echo Docker 可用，啟動容器...
    docker-compose up -d
    echo 容器啟動完成
)
pause
goto MENU

:PHASE5_MANAGER
echo Phase 5 管理系統...
echo ==========================================
echo Phase 5 商業化與生態擴展管理
python scripts/phase5_launch.py --stage=all
pause
goto MENU

:SYSTEM_STATUS
echo 系統狀態檢查...
echo ==========================================
echo Phase 4 狀態: 100%% 完成 (企業級技術基礎)
echo Phase 5 狀態: 已啟動 (商業化與生態擴展)
echo.
echo 核心功能:
echo   用戶管理系統 (註冊/登入/權限)
echo   AI 股價預測 (LSTM 深度學習)
echo   三層訂閱方案 (免費/專業/企業)
echo   統一導航系統
echo   Docker 容器化
echo.
echo 下週重點: AI 智能化升級與技術深化
echo.
echo Python 版本:
python --version
echo.
echo 檔案結構檢查:
if exist "pages/enhanced/00_User_Center.py" (echo 用戶中心: 存在) else (echo 用戶中心: 缺失)
if exist "pages/enhanced/advanced/08_AI_Stock_Predictor.py" (echo AI 預測: 存在) else (echo AI 預測: 缺失)
if exist "business/" (echo 商業化目錄: 存在) else (echo 商業化目錄: 缺失)
if exist "api/" (echo API 目錄: 存在) else (echo API 目錄: 缺失)
pause
goto MENU

:HELP
echo 幫助信息
echo ==========================================
echo JoJo Trading v5.0.0 Professional Edition
echo AI 驅動的專業投資分析平台
echo.
echo 使用指南:
echo   1. 主應用: 完整功能入口，推薦新用戶使用
echo   2. 用戶中心: 註冊帳號、選擇訂閱方案
echo   3. 主導航: 智能功能導航系統
echo   4. AI 預測: LSTM 深度學習股價預測 (需專業版)
echo   5. DCF 計算: 現金流折現估值分析
echo   6. Docker: 容器化部署 (需安裝 Docker)
echo   7. Phase 5: 商業化開發管理工具
echo   8. 系統狀態: 檢查專案完成度和環境
echo.
echo 訂閱方案:
echo   免費版: 基礎 DCF 計算 (10次/月)
echo   專業版: $29/月，無限 DCF + AI 分析
echo   企業版: $99/月，完整 API + 白標方案
echo.
echo 技術支援:
echo   Email: support@jojo-trading.com
echo   文檔: https://docs.jojo-trading.com
echo   問題: https://github.com/jojo-trading/issues
pause
goto MENU

:EXIT
echo.
echo 感謝使用 JoJo Trading v5.0.0 Professional！
echo 目標: 打造世界級的 AI 投資分析平台
echo Phase 5: 商業化與生態系統擴展成功啟動
echo.
pause
exit /b 0
