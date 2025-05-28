# GitHub 部署指南 - JoJotrading Phase 1

## 🚀 快速部署步驟

### 1. 建立 GitHub 倉庫

1. 前往 [GitHub](https://github.com) 並登入
2. 點擊 "New repository" 創建新倉庫
3. 倉庫名稱：`jojo_trading` 或您偏好的名稱
4. 設為 Public 或 Private（依需求）
5. **不要**勾選 "Initialize with README"（因為本地已有 README）
6. 點擊 "Create repository"

### 2. 更新遠程倉庫設置

在 PowerShell 中執行以下指令，將 `YOUR_GITHUB_USERNAME` 替換為您的 GitHub 用戶名：

```powershell
cd "d:\AI_Park\Workspace\dev_projects\web\jojo_trading"

# 移除現有的遠程設置
git remote remove origin

# 添加您的實際 GitHub 倉庫
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/jojo_trading.git

# 驗證遠程設置
git remote -v
```

### 3. 推送到 GitHub

```powershell
# 推送主分支到 GitHub
git push -u origin main

# 如果遇到錯誤，可能需要強制推送（首次推送時）
git push -u origin main --force
```

### 4. 驗證部署

1. 前往您的 GitHub 倉庫頁面
2. 確認所有檔案都已上傳
3. 檢查 README.md 是否正確顯示

## 🔧 自動化部署腳本

### Windows PowerShell 版本

創建 `deploy_to_github.ps1` 檔案：

```powershell
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
git push -u origin main --force

Write-Host "✅ 部署完成！" -ForegroundColor Green
Write-Host "🌐 倉庫連結: https://github.com/$GitHubUsername/$RepoName" -ForegroundColor Cyan
```

### 使用方法

1. 保存上述腳本為 `deploy_to_github.ps1`
2. 在 PowerShell 中執行：

```powershell
# 範例：將 YOUR_USERNAME 替換為您的 GitHub 用戶名
.\deploy_to_github.ps1 -GitHubUsername "YOUR_USERNAME"

# 或指定自訂倉庫名稱
.\deploy_to_github.ps1 -GitHubUsername "YOUR_USERNAME" -RepoName "my_jojo_trading"
```

## 🔒 驗證與權限

### GitHub 個人存取權杖（如需要）

如果推送時遇到權限問題，您可能需要設置個人存取權杖：

1. 前往 GitHub Settings > Developer settings > Personal access tokens
2. 點擊 "Generate new token (classic)"
3. 選擇適當的權限（repo 權限）
4. 生成權杖並保存

使用權杖推送：
```powershell
git remote set-url origin https://YOUR_TOKEN@github.com/YOUR_USERNAME/jojo_trading.git
git push -u origin main
```

## 📋 部署檢查清單

- [ ] GitHub 倉庫已創建
- [ ] 遠程倉庫 URL 已正確設置
- [ ] 所有 Phase 1 檔案都已提交
- [ ] README.md 正確顯示 Phase 1 功能
- [ ] 推送成功完成
- [ ] GitHub 倉庫頁面顯示所有檔案

## 🎯 下一步

部署完成後，您可以：

1. **設置 GitHub Pages**（如果需要網頁展示）
2. **添加協作者**（如果是團隊專案）
3. **設置 Issues 和 Projects**（專案管理）
4. **配置 GitHub Actions**（自動化部署）

## 📞 疑難排解

### 常見問題

1. **推送被拒絕**
   ```powershell
   git push -u origin main --force
   ```

2. **遠程倉庫不存在**
   - 確認 GitHub 倉庫已創建
   - 檢查倉庫名稱拼寫

3. **權限問題**
   - 使用個人存取權杖
   - 確認 GitHub 帳號權限

4. **本地更改衝突**
   ```powershell
   git status
   git add .
   git commit -m "Fix conflicts"
   ```

---

**準備推送您的 JoJotrading Phase 1 優化版本到 GitHub！** 🚀
