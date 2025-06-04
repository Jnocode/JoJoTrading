@echo off
echo JoJo Trading 系統啟動腳本
echo ==========================

echo 檢查 Python 環境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 錯誤：未找到 Python，請先安裝 Python 3.8+
    pause
    exit /b 1
)

echo 檢查依賴...
pip show streamlit >nul 2>&1
if errorlevel 1 (
    echo 安裝依賴中...
    pip install -r requirements.txt
)

echo 啟動 JoJo Trading Web 介面...
python main.py

pause
