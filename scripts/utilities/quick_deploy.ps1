#!/usr/bin/env pwsh
# JoJo Trading v1.0.0 - 快速部署腳本

Write-Host "🚀 JoJo Trading v1.0.0 - 快速部署腳本" -ForegroundColor Green
Write-Host "=======================================" -ForegroundColor Green

# 進入專案目錄
Set-Location "d:\AI_Park\Workspace\dev_projects\web\jojo_trading"

# 檢查 Git 狀態
Write-Host "`n📊 檢查 Git 狀態..." -ForegroundColor Yellow
git status --short

# 顯示當前提交
Write-Host "`n📝 最近的提交記錄:" -ForegroundColor Yellow
git log --oneline -3

# 顯示標籤
Write-Host "`n🏷️ 版本標籤:" -ForegroundColor Yellow
git tag -l

Write-Host "`n🎯 GitHub 部署步驟:" -ForegroundColor Cyan
Write-Host "1. 訪問: https://github.com/new" -ForegroundColor White
Write-Host "2. 倉庫名稱: jojo-trading" -ForegroundColor White
Write-Host "3. 描述: 基於 DCF 估值的台股篩選系統 - JoJo Trading v1.0.0" -ForegroundColor White
Write-Host "4. 選擇 Public 或 Private" -ForegroundColor White
Write-Host "5. 不要勾選任何初始化選項" -ForegroundColor White

Write-Host "`n🔧 部署命令 (創建倉庫後執行):" -ForegroundColor Yellow
Write-Host "替換 YOUR_USERNAME 為您的 GitHub 用戶名：" -ForegroundColor Gray
Write-Host ""
Write-Host "git remote add origin https://github.com/YOUR_USERNAME/jojo-trading.git" -ForegroundColor Green
Write-Host "git push -u origin main" -ForegroundColor Green  
Write-Host "git push origin --tags" -ForegroundColor Green
Write-Host ""

# 檢查是否已設定遠端倉庫
$remotes = git remote -v 2>$null
if ($remotes) {
    Write-Host "🔗 已設定的遠端倉庫:" -ForegroundColor Yellow
    Write-Host $remotes -ForegroundColor White
    
    Write-Host "`n⚡ 快速推送選項:" -ForegroundColor Cyan
    $pushConfirm = Read-Host "是否要立即推送? (y/N)"
    if ($pushConfirm -eq "y" -or $pushConfirm -eq "Y") {
        Write-Host "`n🚀 推送中..." -ForegroundColor Green
        try {
            git push -u origin main
            git push origin --tags
            Write-Host "✅ 推送完成！" -ForegroundColor Green
        } catch {
            Write-Host "❌ 推送失敗，請檢查網路連接與權限" -ForegroundColor Red
        }
    }
} else {
    Write-Host "ℹ️ 尚未設定遠端倉庫，請先在 GitHub 創建倉庫" -ForegroundColor Blue
}

Write-Host "`n🎉 JoJo Trading v1.0.0 準備就緒！" -ForegroundColor Green
Write-Host "📖 詳細說明請參考: DEPLOY_TO_GITHUB.md" -ForegroundColor Gray
