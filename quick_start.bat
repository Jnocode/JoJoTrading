@echo off
echo 正在啟動JoJoTrading系統...
cd /d "d:\AI_Park\Workspace\dev_projects\web\jojo_trading"

echo 檢查虛擬環境...
if exist ".venv_new\Scripts\activate.bat" (
    echo 啟動虛擬環境...
    call .venv_new\Scripts\activate.bat
) else (
    echo 虛擬環境不存在，嘗試原虛擬環境...
    if exist ".venv\Scripts\activate.bat" (
        call .venv\Scripts\activate.bat
    ) else (
        echo 找不到虛擬環境！
        pause
        exit /b 1
    )
)

echo 檢查Streamlit...
python -c "import streamlit; print('Streamlit已安裝，版本:', streamlit.__version__)"
if errorlevel 1 (
    echo 正在安裝Streamlit...
    pip install streamlit
)

echo 啟動JoJoTrading應用...
echo 請稍候，應用將在 http://localhost:8506 開啟
streamlit run app.py --server.port 8506 --server.headless false

pause
