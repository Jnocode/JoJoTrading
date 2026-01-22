# JoJo Trading v5.0.0 Professional Edition
# Phase 5: 商業化與生態系統擴展

Write-Host "===========================================" -ForegroundColor Green
Write-Host " JoJo Trading v5.0.0 Professional" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Green
Write-Host " Phase 5: 商業化與生態系統擴展" -ForegroundColor Yellow
Write-Host ""

# 檢查 Python 環境
Write-Host "檢查 Python 環境..." -ForegroundColor Yellow
$PYTHON_CMD = "python"
if (Test-Path ".venv\Scripts\python.exe") {
    $PYTHON_CMD = ".\.venv\Scripts\python.exe"
    Write-Host "✅ 使用虛擬環境: $PYTHON_CMD" -ForegroundColor Green
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $PYTHON_CMD = "python"
    Write-Host "✅ 使用系統 Python" -ForegroundColor Green
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $PYTHON_CMD = "py"
    Write-Host "✅ 使用 Python Launcher (py)" -ForegroundColor Green
} else {
    Write-Host "❌ Python 未安裝或不可用" -ForegroundColor Red
    exit 1
}

# 主選單函數
function Show-Menu {
    Clear-Host
    Write-Host ""
    Write-Host "===========================================" -ForegroundColor Green
    Write-Host " JoJo Trading v5.0.0 Professional" -ForegroundColor Cyan
    Write-Host "===========================================" -ForegroundColor Green
    Write-Host " AI 驅動投資分析平台" -ForegroundColor Magenta
    Write-Host ""
    Write-Host "請選擇啟動模式:" -ForegroundColor White
    Write-Host ""
    Write-Host "  1. 🚀 主應用 (streamlit_app.py)" -ForegroundColor White
    Write-Host "  2. 👤 用戶中心 (註冊/登入)" -ForegroundColor White
    Write-Host "  3. 🎯 主導航系統" -ForegroundColor White
    Write-Host "  4. 🤖 AI 股價預測" -ForegroundColor White
    Write-Host "  5. 📊 DCF 估值計算" -ForegroundColor White
    Write-Host "  6. 🐳 Docker 容器啟動" -ForegroundColor White
    Write-Host "  7. 🔧 Phase 5 管理" -ForegroundColor White
    Write-Host "  8. 📈 系統狀態" -ForegroundColor White
    Write-Host "  9. ❓ 幫助信息" -ForegroundColor White
    Write-Host "  0. 🚪 退出" -ForegroundColor White
    Write-Host ""
    Write-Host "===========================================" -ForegroundColor Green
}

# 主循環
do {
    Show-Menu
    $choice = Read-Host "請輸入選項 (0-9)"
    
    switch ($choice) {
        "1" {
            Write-Host "🚀 啟動主應用..." -ForegroundColor Green
            Write-Host "這是 JoJo Trading 的主入口，包含完整功能導航" -ForegroundColor Yellow
            & $PYTHON_CMD -m streamlit run main_app.py
            Read-Host "按 Enter 鍵返回主選單..."
        }
        "2" {
            Write-Host "👤 啟動用戶中心..." -ForegroundColor Green
            Write-Host "用戶註冊、登入、訂閱管理" -ForegroundColor Yellow
            if (Test-Path "pages/enhanced/00_User_Center.py") {
                & $PYTHON_CMD -m streamlit run pages/enhanced/00_User_Center.py
            } else {
                & $PYTHON_CMD -m streamlit run "pages/enhanced/00_👤_User_Center.py"
            }
            Read-Host "按 Enter 鍵返回主選單..."
        }
        "3" {
            Write-Host "🎯 啟動主導航系統..." -ForegroundColor Green
            Write-Host "智能功能導航與快速入口" -ForegroundColor Yellow
            if (Test-Path "pages/enhanced/00_Navigation.py") {
                & $PYTHON_CMD -m streamlit run pages/enhanced/00_Navigation.py
            } else {
                & $PYTHON_CMD -m streamlit run "pages/enhanced/00_🎯_Navigation.py"
            }
            Read-Host "按 Enter 鍵返回主選單..."
        }
        "4" {
            Write-Host "🤖 啟動 AI 股價預測..." -ForegroundColor Green
            Write-Host "LSTM 深度學習股價預測 (需專業版)" -ForegroundColor Yellow
            if (Test-Path "pages/enhanced/advanced/08_AI_Stock_Predictor.py") {
                & $PYTHON_CMD -m streamlit run pages/enhanced/advanced/08_AI_Stock_Predictor.py
            } else {
                & $PYTHON_CMD -m streamlit run "pages/enhanced/advanced/08_🤖_AI_Stock_Predictor.py"
            }
            Read-Host "按 Enter 鍵返回主選單..."
        }
        "5" {
            Write-Host "📊 啟動 DCF 估值計算器..." -ForegroundColor Green
            Write-Host "現金流折現估值分析" -ForegroundColor Yellow
            if (Test-Path "pages/enhanced/02_DCF_Calculator.py") {
                & $PYTHON_CMD -m streamlit run pages/enhanced/02_DCF_Calculator.py
            } else {
                & $PYTHON_CMD -m streamlit run "pages/enhanced/02_📊_DCF_Calculator.py"
            }
            Read-Host "按 Enter 鍵返回主選單..."
        }
        "6" {
            Write-Host "🐳 啟動 Docker 容器..." -ForegroundColor Green
            try {
                docker --version | Out-Null
                Write-Host "✅ Docker 可用，啟動容器..." -ForegroundColor Green
                docker-compose up -d
                Write-Host "✅ 容器啟動完成" -ForegroundColor Green
            } catch {
                Write-Host "❌ Docker 未安裝或未啟動" -ForegroundColor Red
                Write-Host "請先安裝 Docker Desktop" -ForegroundColor Yellow
            }
            Read-Host "按 Enter 鍵返回主選單..."
        }
        "7" {
            Write-Host "🔧 Phase 5 管理系統..." -ForegroundColor Green
            & $PYTHON_CMD scripts/phase5_launch.py --stage=all
            Read-Host "按 Enter 鍵返回主選單..."
        }
        "8" {
            Write-Host "📈 系統狀態檢查..." -ForegroundColor Green
            Write-Host "📊 Phase 4 狀態: ✅ 100% 完成 (企業級技術基礎)" -ForegroundColor Green
            Write-Host "🚀 Phase 5 狀態: 已啟動 (商業化與生態擴展)" -ForegroundColor Green
            Write-Host ""
            Write-Host "📁 核心功能:" -ForegroundColor White
            Write-Host "  ✅ 用戶管理系統 (註冊/登入/權限)" -ForegroundColor Green
            Write-Host "  ✅ AI 股價預測 (LSTM 深度學習)" -ForegroundColor Green
            Write-Host "  ✅ 三層訂閱方案 (免費/專業/企業)" -ForegroundColor Green
            Write-Host "  ✅ 統一導航系統" -ForegroundColor Green
            Write-Host "  ✅ Docker 容器化" -ForegroundColor Green
            Write-Host ""
            Write-Host "🎯 下週重點: AI 智能化升級與技術深化" -ForegroundColor Yellow
            Write-Host ""
            Write-Host "Python 版本:" -ForegroundColor White
            & $PYTHON_CMD --version
            Write-Host ""
            Write-Host "📊 檔案結構檢查:" -ForegroundColor White
            if (Test-Path "pages/enhanced/00_👤_User_Center.py") { Write-Host "  ✅ 用戶中心" -ForegroundColor Green } else { Write-Host "  ❌ 用戶中心" -ForegroundColor Red }
            if (Test-Path "pages/enhanced/advanced/08_🤖_AI_Stock_Predictor.py") { Write-Host "  ✅ AI 預測" -ForegroundColor Green } else { Write-Host "  ❌ AI 預測" -ForegroundColor Red }
            if (Test-Path "business/") { Write-Host "  ✅ 商業化目錄" -ForegroundColor Green } else { Write-Host "  ❌ 商業化目錄" -ForegroundColor Red }
            if (Test-Path "api/") { Write-Host "  ✅ API 目錄" -ForegroundColor Green } else { Write-Host "  ❌ API 目錄" -ForegroundColor Red }
            Read-Host "按 Enter 鍵返回主選單..."
        }
        "9" {
            Write-Host "❓ 幫助信息" -ForegroundColor Green
            Write-Host "JoJo Trading v5.0.0 Professional Edition" -ForegroundColor Cyan
            Write-Host "AI 驅動的專業投資分析平台" -ForegroundColor Magenta
            Write-Host ""
            Write-Host "📚 使用指南:" -ForegroundColor White
            Write-Host "  1. 主應用: 完整功能入口，推薦新用戶使用" -ForegroundColor Gray
            Write-Host "  2. 用戶中心: 註冊帳號、選擇訂閱方案" -ForegroundColor Gray
            Write-Host "  3. 主導航: 智能功能導航系統" -ForegroundColor Gray
            Write-Host "  4. AI 預測: LSTM 深度學習股價預測 (需專業版)" -ForegroundColor Gray
            Write-Host "  5. DCF 計算: 現金流折現估值分析" -ForegroundColor Gray
            Write-Host "  6. Docker: 容器化部署 (需安裝 Docker)" -ForegroundColor Gray
            Write-Host "  7. Phase 5: 商業化開發管理工具" -ForegroundColor Gray
            Write-Host "  8. 系統狀態: 檢查專案完成度和環境" -ForegroundColor Gray
            Write-Host ""
            Write-Host "💎 訂閱方案:" -ForegroundColor White
            Write-Host "  🆓 免費版: 基礎 DCF 計算 (10次/月)" -ForegroundColor Green
            Write-Host "  💰 專業版: `$29/月，無限 DCF + AI 分析" -ForegroundColor Yellow
            Write-Host "  🏢 企業版: `$99/月，完整 API + 白標方案" -ForegroundColor Red
            Write-Host ""
            Write-Host "🆘 技術支援:" -ForegroundColor White
            Write-Host "  📧 Email: support@jojo-trading.com" -ForegroundColor Gray
            Write-Host "  📚 文檔: https://docs.jojo-trading.com" -ForegroundColor Gray
            Write-Host "  🐛 問題: https://github.com/jojo-trading/issues" -ForegroundColor Gray
            Read-Host "按 Enter 鍵返回主選單..."
        }
        "0" {
            Write-Host ""
            Write-Host "👋 感謝使用 JoJo Trading v5.0.0 Professional！" -ForegroundColor Green
            Write-Host "🎯 目標: 打造世界級的 AI 投資分析平台" -ForegroundColor Yellow
            Write-Host "📈 Phase 5: 商業化與生態系統擴展成功啟動" -ForegroundColor Cyan
            Write-Host ""
            break
        }
        default {
            Write-Host "❌ 無效選項，請重新選擇" -ForegroundColor Red
            Read-Host "按 Enter 鍵繼續..."
        }
    }
} while ($true)
