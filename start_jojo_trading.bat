chcp 65001
@echo off
REM 啟動 JoJo Trading 桌面版（Streamlit Web UI）
cd /d %~dp0

REM 啟動虛擬環境（假設 .venv 存在）
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
) else (
    echo [警告] 找不到 .venv 虛擬環境，請先安裝依賴：
    echo    python -m venv .venv
    echo    .venv\Scripts\activate.bat
    echo    pip install -r requirements.txt
    pause
    exit /b
)

REM 在新 cmd 視窗中執行所有啟動、顯示與開瀏覽器指令，主批次檔本身不再執行任何 Streamlit 相關命令
start "JoJo Trading" cmd /k ".venv\Scripts\python.exe --version && .venv\Scripts\python.exe -m streamlit --version && .venv\Scripts\python.exe -m streamlit run app.py --server.headless false && start http://localhost:8501 && echo JoJo Trading 啟動中... 請稍候瀏覽器自動開啟。 && pause"

REM 主批次檔結束，不再重複執行 Streamlit
exit /b
