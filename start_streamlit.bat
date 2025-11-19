@echo off
chcp 65001 >nul 2>&1
title JoJo Trading v3.0.0 - Streamlit App
color 0A

echo.
echo ==========================================
echo    JoJo Trading v3.0.0 - Streamlit App
echo ==========================================
echo    專業級投資分析平台
echo.

cd /d "%~dp0"

echo [啟動] 正在啟動 Streamlit 應用程式...
echo.

if exist ".venv\Scripts\python.exe" (
    echo [成功] 找到虛擬環境: .venv
    echo [執行] 啟動 Streamlit 應用程式...
    echo.
    
    .venv\Scripts\python.exe -m streamlit run streamlit_app.py --server.port 8501
    
) else (
    echo [錯誤] 找不到虛擬環境，請先執行 start.bat 設置環境
    pause
)

echo.
echo [完成] 應用程式已結束
pause
