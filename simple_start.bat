@echo off
REM 簡化版 JoJoTrading 啟動腳本
REM 解決 PowerShell 執行問題

echo.
echo ========================================
echo     JoJoTrading 系統啟動中...
echo ========================================
echo.

REM 設置編碼
chcp 65001 >nul

REM 切換目錄
cd /d "%~dp0"
echo 當前目錄: %CD%

REM 檢查虛擬環境
echo.
echo 正在檢查虛擬環境...
if exist ".venv_new\Scripts\activate.bat" (
    echo ✓ 找到 .venv_new 虛擬環境
    call .venv_new\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    echo ✓ 找到 .venv 虛擬環境  
    call .venv\Scripts\activate.bat
) else (
    echo ✗ 找不到虛擬環境！
    echo.
    echo 請先執行以下命令創建虛擬環境：
    echo python -m venv .venv_new
    echo .venv_new\Scripts\activate.bat
    echo pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

REM 檢查 Python
echo.
echo 正在檢查 Python...
python --version
if errorlevel 1 (
    echo ✗ Python 未正確安裝！
    pause
    exit /b 1
)

REM 檢查 Streamlit
echo.
echo 正在檢查 Streamlit...
python -c "import streamlit" 2>nul
if errorlevel 1 (
    echo ✗ Streamlit 未安裝，正在安裝...
    pip install streamlit
    if errorlevel 1 (
        echo ✗ Streamlit 安裝失敗！
        pause
        exit /b 1
    )
    echo ✓ Streamlit 安裝完成
) else (
    echo ✓ Streamlit 已安裝
)

REM 啟動系統
echo.
echo ========================================
echo       啟動 JoJoTrading 系統
echo ========================================
echo.
echo 💡 系統功能：
echo    • 台股 DCF 估值分析
echo    • 成長股智能篩選 (4種配置)
echo    • 財務數據異常偵測
echo.
echo 🌐 訪問地址: http://localhost:8506
echo.
echo 正在啟動 Streamlit...
echo (請稍候，啟動需要10-15秒)
echo.

REM 啟動 Streamlit
python -m streamlit run app.py --server.port 8506 --server.headless false

REM 如果到達這裡，表示 Streamlit 已停止
echo.
echo JoJoTrading 系統已停止
pause
