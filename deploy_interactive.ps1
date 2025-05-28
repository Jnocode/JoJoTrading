# JoJoTrading 互動式 GitHub 部署腳本
# 作者：GitHub Copilot AI Assistant
# 描述：互動式部署 JoJoTrading 專案到 GitHub

param(
    [Parameter(Mandatory=$false)]
    [string]$GitHubUsername,
    
    [Parameter(Mandatory=$false)]
    [string]$RepoName = "jojo_trading"
)

function Write-ColorMessage {
    param($Message, $Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

function Get-UserInput {
    param($Prompt, $DefaultValue = "")
    if ($DefaultValue) {
        $input = Read-Host "$Prompt [$DefaultValue]"
        return if ($input) { $input } else { $DefaultValue }
    } else {
        return Read-Host $Prompt
    }
}

# 標題
Write-ColorMessage "🚀 JoJoTrading 互動式 GitHub 部署腳本" "Cyan"
Write-ColorMessage "==========================================" "Cyan"

# 檢查是否在正確的目錄
$currentPath = Get-Location
$projectPath = "d:\AI_Park\Workspace\dev_projects\web\jojo_trading"

if (!(Test-Path "app.py") -or !(Test-Path "jojo_state_machine.py")) {
    Write-ColorMessage "❌ 錯誤：請在 JoJoTrading 專案根目錄執行此腳本" "Red"
    Write-ColorMessage "   當前路徑：$currentPath" "Yellow"
    Write-ColorMessage "   期望路徑：$projectPath" "Yellow"
    
    $switchDir = Get-UserInput "🔄 是否要自動切換到專案目錄？(y/n)" "y"
    if ($switchDir -eq "y" -or $switchDir -eq "Y") {
        if (Test-Path $projectPath) {
            Set-Location $projectPath
            Write-ColorMessage "✅ 已切換到專案目錄" "Green"
        } else {
            Write-ColorMessage "❌ 專案目錄不存在：$projectPath" "Red"
            exit 1
        }
    } else {
        exit 1
    }
}

Write-ColorMessage "✅ 確認在 JoJoTrading 專案目錄" "Green"

# 檢查 Git 狀態
Write-ColorMessage "`n📋 檢查 Git 狀態..." "Yellow"
$gitStatus = git status --porcelain
if ($gitStatus) {
    Write-ColorMessage "📝 發現未提交的更改：" "Yellow"
    git status --short
    
    $commitChanges = Get-UserInput "`n💾 是否要提交這些更改？(y/n)" "y"
    if ($commitChanges -eq "y" -or $commitChanges -eq "Y") {
        git add .
        $commitMsg = Get-UserInput "📝 輸入提交訊息" "🔧 自動提交：部署前的最後更改"
        git commit -m $commitMsg
        Write-ColorMessage "✅ 更改已提交" "Green"
    }
} else {
    Write-ColorMessage "✅ 沒有未提交的更改" "Green"
}

# 獲取 GitHub 用戶名
if (-not $GitHubUsername) {
    Write-ColorMessage "`n👤 GitHub 設定" "Cyan"
    $GitHubUsername = Get-UserInput "請輸入您的 GitHub 用戶名"
    
    if (-not $GitHubUsername) {
        Write-ColorMessage "❌ 必須提供 GitHub 用戶名" "Red"
        exit 1
    }
}

# 確認倉庫名稱
$RepoName = Get-UserInput "📦 確認倉庫名稱" $RepoName

# 顯示部署信息
Write-ColorMessage "`n📋 部署信息確認：" "Cyan"
Write-ColorMessage "   GitHub 用戶名：$GitHubUsername" "White"
Write-ColorMessage "   倉庫名稱：$RepoName" "White"
Write-ColorMessage "   倉庫 URL：https://github.com/$GitHubUsername/$RepoName" "White"

$confirm = Get-UserInput "`n🚀 確認開始部署？(y/n)" "y"
if ($confirm -ne "y" -and $confirm -ne "Y") {
    Write-ColorMessage "❌ 部署已取消" "Yellow"
    exit 0
}

# 設置遠程倉庫
$repoUrl = "https://github.com/$GitHubUsername/$RepoName.git"
Write-ColorMessage "`n🔗 設置遠程倉庫..." "Yellow"

# 檢查當前遠程設置
$currentRemote = git remote get-url origin 2>$null
if ($currentRemote -and $currentRemote -ne $repoUrl) {
    Write-ColorMessage "🔄 更新遠程倉庫 URL：$repoUrl" "Yellow"
    git remote set-url origin $repoUrl
} elseif (-not $currentRemote) {
    Write-ColorMessage "➕ 添加遠程倉庫：$repoUrl" "Yellow"
    git remote add origin $repoUrl
} else {
    Write-ColorMessage "✅ 遠程倉庫已正確設置" "Green"
}

# 推送到 GitHub
Write-ColorMessage "`n🚀 推送到 GitHub..." "Yellow"
try {
    # 先嘗試正常推送
    $pushResult = git push -u origin main 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-ColorMessage "✅ 部署成功！" "Green"
    } else {
        # 如果推送失敗，詢問是否強制推送
        Write-ColorMessage "⚠️  正常推送失敗，可能是因為遠程倉庫有衝突" "Yellow"
        $forcePush = Get-UserInput "🔄 是否要強制推送？(這會覆蓋遠程倉庫內容)(y/n)" "n"
        
        if ($forcePush -eq "y" -or $forcePush -eq "Y") {
            git push -u origin main --force
            if ($LASTEXITCODE -eq 0) {
                Write-ColorMessage "✅ 強制推送成功！" "Green"
            } else {
                throw "強制推送失敗"
            }
        } else {
            throw "推送被取消"
        }
    }
    
    # 成功訊息
    Write-ColorMessage "`n🎉 部署完成！" "Green"
    Write-ColorMessage "🌐 倉庫連結：https://github.com/$GitHubUsername/$RepoName" "Cyan"
    Write-ColorMessage "📋 請前往 GitHub 檢查所有檔案是否正確上傳" "Yellow"
    Write-ColorMessage "`n📚 下一步建議：" "Cyan"
    Write-ColorMessage "   1. 在 GitHub 上檢查倉庫內容" "White"
    Write-ColorMessage "   2. 設定倉庫描述和主題標籤" "White"
    Write-ColorMessage "   3. 考慮添加 LICENSE 檔案" "White"
    Write-ColorMessage "   4. 設定 GitHub Pages（可選）" "White"
    
} catch {
    Write-ColorMessage "`n❌ 部署失敗：$_" "Red"
    Write-ColorMessage "💡 常見解決方法：" "Yellow"
    Write-ColorMessage "   1. 檢查網路連接" "White"
    Write-ColorMessage "   2. 確認 GitHub 權限設置" "White"
    Write-ColorMessage "   3. 檢查 GitHub 用戶名是否正確" "White"
    Write-ColorMessage "   4. 確認在 GitHub 上已創建同名倉庫" "White"
    Write-ColorMessage "   5. 參考 GITHUB_DEPLOY_GUIDE.md 獲取詳細說明" "White"
    exit 1
}

Write-ColorMessage "`n🎯 感謝使用 JoJoTrading 部署腳本！" "Cyan"
