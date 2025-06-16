@echo off
REM 🐳 JoJo Trading - Docker 快速啟動腳本 (Windows)
REM 自動檢測並啟動最佳的 Docker 環境

setlocal EnableDelayedExpansion

echo.
echo 🚀 JoJo Trading - Docker 環境啟動器
echo ================================================

REM 檢查 Docker 是否安裝並運行
echo 🔍 檢查 Docker 環境...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 錯誤: Docker 未安裝或未啟動
    echo 請先安裝 Docker Desktop 並確保它正在運行
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 錯誤: Docker Compose 未安裝
    echo 請確保 Docker Desktop 包含 Docker Compose
    pause
    exit /b 1
)

echo ✅ Docker 環境正常

REM 選擇環境模式
echo.
echo 🎯 請選擇啟動模式:
echo [1] 開發環境 (Development) - 支援熱重載和調試
echo [2] 生產環境 (Production) - 優化性能和安全性
echo [3] 快速部署 (Quick Deploy) - 自動建構並啟動
echo [4] 清理環境 (Clean Up) - 停止並清理所有容器
echo [0] 退出
echo.

set /p choice="請輸入選項 [1-4,0]: "

if "%choice%"=="1" goto dev_mode
if "%choice%"=="2" goto prod_mode
if "%choice%"=="3" goto quick_deploy
if "%choice%"=="4" goto cleanup
if "%choice%"=="0" goto exit
goto invalid_choice

:dev_mode
echo.
echo 🛠️  啟動開發環境...
echo ================================================
docker-compose up -d
if errorlevel 1 (
    echo ❌ 開發環境啟動失敗
    goto error_exit
)
goto success_dev

:prod_mode
echo.
echo 🚀 啟動生產環境...
echo ================================================
docker-compose -f docker-compose.yml -f docker-compose.prod.yml --profile production up -d
if errorlevel 1 (
    echo ❌ 生產環境啟動失敗
    goto error_exit
)
goto success_prod

:quick_deploy
echo.
echo ⚡ 快速部署模式...
echo ================================================
echo 🏗️  建構 Docker 映像...
docker-compose build
if errorlevel 1 (
    echo ❌ 映像建構失敗
    goto error_exit
)

echo 🛠️  啟動容器...
docker-compose up -d
if errorlevel 1 (
    echo ❌ 容器啟動失敗
    goto error_exit
)
goto success_dev

:cleanup
echo.
echo 🧹 清理 Docker 環境...
echo ================================================
docker-compose down --volumes --remove-orphans
docker image prune -f
docker volume prune -f
echo ✅ 清理完成
goto exit

:success_dev
echo.
echo 🎉 開發環境啟動成功！
echo ================================================
echo 📊 應用程式 URL: http://localhost:8501
echo 📈 Redis 監控: http://localhost:6379
echo 📋 容器狀態: docker-compose ps
echo 📝 查看日誌: docker-compose logs -f jojo-trading
echo.
echo 💡 提示:
echo - 修改代碼後會自動重載
echo - 使用 Ctrl+C 停止容器
echo - 使用 docker-compose down 完全停止
goto wait_and_open

:success_prod
echo.
echo 🎉 生產環境啟動成功！
echo ================================================
echo 📊 應用程式 URL: http://localhost:80
echo 📈 HTTPS URL: https://localhost:443
echo 📊 監控面板: http://localhost:9090
echo 📋 容器狀態: docker-compose ps
echo.
echo 💡 提示:
echo - 生產環境已優化性能和安全性
echo - 使用負載均衡器提供服務
echo - 支援 SSL/HTTPS 連接
goto wait_and_open

:wait_and_open
echo.
echo ⏳ 等待應用程式啟動...
timeout /t 10 /nobreak >nul

REM 檢查應用程式是否正常啟動
curl -f http://localhost:8501/_stcore/health >nul 2>&1
if errorlevel 1 (
    echo ⚠️  警告: 應用程式可能還在啟動中
    echo 請稍等片刻後手動訪問 http://localhost:8501
) else (
    echo ✅ 應用程式健康檢查通過
    echo 🌐 正在開啟瀏覽器...
    start http://localhost:8501
)
goto exit

:invalid_choice
echo ❌ 無效選項，請重新選擇
goto exit

:error_exit
echo.
echo ❌ 操作失敗，請檢查錯誤訊息
echo 💡 常見問題解決方法:
echo - 確保 Docker Desktop 正在運行
echo - 檢查端口 8501 是否被占用
echo - 嘗試執行: docker-compose down 後重新啟動
echo - 查看詳細日誌: docker-compose logs
pause
exit /b 1

:exit
echo.
echo 👋 感謝使用 JoJo Trading Docker 啟動器！
echo 如有問題，請查看文檔或聯繫開發團隊。
pause
exit /b 0
