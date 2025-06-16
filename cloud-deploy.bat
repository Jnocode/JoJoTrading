@echo off
REM 🚀 JoJo Trading 雲端部署管理器 - Windows 批次檔
REM 提供友好的命令行界面來管理多雲端部署

setlocal EnableDelayedExpansion

echo.
echo ============================================
echo 🚀 JoJo Trading 雲端部署管理器
echo ============================================
echo.

REM 檢查 Python 是否可用
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Python 未安裝或未加入 PATH
    echo 請安裝 Python 3.8+ 並確保加入系統 PATH
    pause
    exit /b 1
)

REM 如果沒有提供參數，顯示互動菜單
if "%1"=="" goto :interactive_menu

REM 直接執行命令
python "%~dp0cloud_deployment_manager.py" %*
goto :end

:interactive_menu
echo 請選擇要執行的操作：
echo.
echo 1. 部署到 AWS ECS
echo 2. 部署到 Azure Container Instances  
echo 3. 部署到 Kubernetes
echo 4. 部署到所有平台
echo 5. 查看 AWS 狀態
echo 6. 查看 Azure 狀態
echo 7. 查看 Kubernetes 狀態
echo 8. 查看所有平台狀態
echo 9. 清理 AWS 資源
echo 10. 清理 Azure 資源
echo 11. 清理 Kubernetes 資源
echo 12. 清理所有平台資源
echo 0. 退出
echo.

set /p choice="請輸入選項 (0-12): "

if "%choice%"=="1" (
    echo.
    echo 🚀 部署到 AWS ECS...
    python "%~dp0cloud_deployment_manager.py" deploy aws
) else if "%choice%"=="2" (
    echo.
    echo 🚀 部署到 Azure Container Instances...
    python "%~dp0cloud_deployment_manager.py" deploy azure
) else if "%choice%"=="3" (
    echo.
    echo 🚀 部署到 Kubernetes...
    python "%~dp0cloud_deployment_manager.py" deploy kubernetes
) else if "%choice%"=="4" (
    echo.
    echo 🚀 部署到所有平台...
    python "%~dp0cloud_deployment_manager.py" deploy all
) else if "%choice%"=="5" (
    echo.
    echo 📊 查看 AWS 狀態...
    python "%~dp0cloud_deployment_manager.py" status aws
) else if "%choice%"=="6" (
    echo.
    echo 📊 查看 Azure 狀態...
    python "%~dp0cloud_deployment_manager.py" status azure
) else if "%choice%"=="7" (
    echo.
    echo 📊 查看 Kubernetes 狀態...
    python "%~dp0cloud_deployment_manager.py" status kubernetes
) else if "%choice%"=="8" (
    echo.
    echo 📊 查看所有平台狀態...
    python "%~dp0cloud_deployment_manager.py" status all
) else if "%choice%"=="9" (
    echo.
    echo 🧹 清理 AWS 資源...
    set /p confirm="確定要清理 AWS 資源嗎？(y/N): "
    if /i "!confirm!"=="y" (
        python "%~dp0cloud_deployment_manager.py" cleanup aws
    ) else (
        echo 操作已取消
    )
) else if "%choice%"=="10" (
    echo.
    echo 🧹 清理 Azure 資源...
    set /p confirm="確定要清理 Azure 資源嗎？(y/N): "
    if /i "!confirm!"=="y" (
        python "%~dp0cloud_deployment_manager.py" cleanup azure
    ) else (
        echo 操作已取消
    )
) else if "%choice%"=="11" (
    echo.
    echo 🧹 清理 Kubernetes 資源...
    set /p confirm="確定要清理 Kubernetes 資源嗎？(y/N): "
    if /i "!confirm!"=="y" (
        python "%~dp0cloud_deployment_manager.py" cleanup kubernetes
    ) else (
        echo 操作已取消
    )
) else if "%choice%"=="12" (
    echo.
    echo 🧹 清理所有平台資源...
    set /p confirm="確定要清理所有平台資源嗎？這將刪除所有部署！(y/N): "
    if /i "!confirm!"=="y" (
        python "%~dp0cloud_deployment_manager.py" cleanup all
    ) else (
        echo 操作已取消
    )
) else if "%choice%"=="0" (
    echo 再見！
    goto :end
) else (
    echo ❌ 無效的選項，請重新選擇
    pause
    goto :interactive_menu
)

echo.
echo ============================================
echo 操作完成
echo ============================================
pause

:end
endlocal
