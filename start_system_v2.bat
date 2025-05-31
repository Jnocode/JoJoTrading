@echo off
chcp 65001
echo.
echo ==========================================
echo    JoJoTrading 成長股優化系統啟動中...
echo ==========================================
echo.

REM 切換到項目目錄
cd /d "d:\AI_Park\Workspace\dev_projects\web\jojo_trading"

REM 檢查並啟動虛擬環境
echo [1/4] 檢查虛擬環境...
if exist ".venv_new\Scripts\activate.bat" (
    echo 找到 .venv_new 虛擬環境，正在啟動...
    call .venv_new\Scripts\activate.bat
    goto :check_deps
) else if exist ".venv\Scripts\activate.bat" (
    echo 找到 .venv 虛擬環境，正在啟動...
    call .venv\Scripts\activate.bat
    goto :check_deps
) else (
    echo [錯誤] 找不到虛擬環境！
    echo 請先執行: python -m venv .venv_new
    pause
    exit /b 1
)

:check_deps
echo.
echo [2/4] 檢查依賴套件...
python -c "import streamlit; print('✓ Streamlit 已安裝，版本:', streamlit.__version__)" 2>nul
if errorlevel 1 (
    echo [警告] Streamlit 未安裝，正在安裝...
    pip install streamlit
    if errorlevel 1 (
        echo [錯誤] Streamlit 安裝失敗！
        pause
        exit /b 1
    )
)

echo.
echo [3/4] 檢查應用程式...
python -c "import app; print('✓ 應用程式模組載入成功')" 2>nul
if errorlevel 1 (
    echo [錯誤] 應用程式模組載入失敗！
    echo 請檢查 app.py 文件是否存在錯誤
    pause
    exit /b 1
)

echo.
echo [4/4] 啟動 JoJoTrading 系統...
echo ✓ 系統將在 http://localhost:8506 啟動
echo ✓ 成長股優化功能已整合完成
echo.
echo 請稍候瀏覽器自動開啟...
timeout /t 2 /nobreak >nul

REM 啟動 Streamlit (背景模式)
start "" /min cmd /c "call .venv_new\Scripts\activate.bat 2>nul || call .venv\Scripts\activate.bat 2>nul && python -m streamlit run app.py --server.port 8506 --server.headless false"

REM 等待服務啟動
timeout /t 5 /nobreak >nul

REM 開啟瀏覽器
start "" "http://localhost:8506"

echo.
echo ==========================================
echo   JoJoTrading 系統啟動完成！
echo ==========================================
echo.
echo 功能特色：
echo • 台股 DCF 估值分析
echo • 成長股智能篩選 (4種預設配置)
echo • 財務數據異常偵測
echo • 互動式狀態機介面
echo.
echo 如需停止系統，請關閉瀏覽器頁面或按 Ctrl+C
echo.
pause
