param(
    [Parameter(Mandatory=$true)]
    [string]$GitHubUsername,
    
    [Parameter(Mandatory=$false)]
    [string]$RepoName = "jojo_trading",
    
    [Parameter(Mandatory=$false)]
    [string]$CommitMessage = "🚀 Deploy: JoJotrading Phase 1 優化版本"
)

Write-Host "🚀 JoJotrading GitHub 部署腳本" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green

# 切換到專案目錄
$ProjectPath = "d:\AI_Park\Workspace\dev_projects\web\jojo_trading"
Set-Location $ProjectPath

Write-Host "📁 當前目錄: $ProjectPath" -ForegroundColor Yellow

# 檢查 Git 狀態
Write-Host "🔍 檢查 Git 狀態..." -ForegroundColor Yellow
git status

# 添加所有更改
Write-Host "📦 添加所有更改到 Git..." -ForegroundColor Yellow
git add .

# 創建提交
Write-Host "💾 創建提交..." -ForegroundColor Yellow
git commit -m $CommitMessage

# 設置遠程倉庫
$RepoUrl = "https://github.com/$GitHubUsername/$RepoName.git"
Write-Host "🔗 設置遠程倉庫: $RepoUrl" -ForegroundColor Yellow

# 移除現有遠程設置並添加新的
git remote remove origin 2>$null
git remote add origin $RepoUrl

# 推送到 GitHub
Write-Host "🚀 推送到 GitHub..." -ForegroundColor Yellow
try {
    git push -u origin main --force
    Write-Host "✅ 部署完成！" -ForegroundColor Green
    Write-Host "🌐 倉庫連結: https://github.com/$GitHubUsername/$RepoName" -ForegroundColor Cyan
    Write-Host "📋 請前往 GitHub 檢查所有檔案是否正確上傳" -ForegroundColor Yellow
} catch {
    Write-Host "❌ 推送失敗，請檢查網路連接與 GitHub 權限" -ForegroundColor Red
    Write-Host "💡 如需權限驗證，請參考 GITHUB_DEPLOY_GUIDE.md" -ForegroundColor Yellow
}
