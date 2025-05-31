# JoJo Trading PowerShell 便利腳本
# 使用方式: .\make.ps1 <command>

param(
    [Parameter(Position=0)]
    [string]$Command = "help"
)

function Show-Help {
    Write-Host "JoJo Trading 可用命令:" -ForegroundColor Green
    Write-Host ""
    Write-Host "  install       安裝基礎依賴"
    Write-Host "  install-dev   安裝開發依賴"
    Write-Host "  test          執行所有測試"
    Write-Host "  test-unit     執行單元測試"
    Write-Host "  test-int      執行整合測試"
    Write-Host "  lint          代碼檢查"
    Write-Host "  format        代碼格式化"
    Write-Host "  clean         清理臨時檔案"
    Write-Host "  run           啟動 Web UI"
    Write-Host "  run-cli       啟動 CLI 模式"
    Write-Host "  build         建置套件"
    Write-Host ""
}

function Install-Base {
    Write-Host "安裝基礎依賴..." -ForegroundColor Yellow
    pip install -r requirements/base.txt
}

function Install-Dev {
    Write-Host "安裝開發依賴..." -ForegroundColor Yellow
    pip install -r requirements/base.txt
    pip install -r requirements/dev.txt
    pip install -r requirements/test.txt
    pip install -e .
}

function Run-Tests {
    Write-Host "執行所有測試..." -ForegroundColor Yellow
    python -m pytest tests/ -v --cov=src/jojo_trading --cov-report=html --cov-report=term
}

function Run-UnitTests {
    Write-Host "執行單元測試..." -ForegroundColor Yellow
    python -m pytest tests/unit/ -v
}

function Run-IntegrationTests {
    Write-Host "執行整合測試..." -ForegroundColor Yellow
    python -m pytest tests/integration/ -v
}

function Run-Lint {
    Write-Host "執行代碼檢查..." -ForegroundColor Yellow
    flake8 src/ tests/
    mypy src/
}

function Format-Code {
    Write-Host "格式化代碼..." -ForegroundColor Yellow
    black src/ tests/
    isort src/ tests/
}

function Clean-Project {
    Write-Host "清理臨時檔案..." -ForegroundColor Yellow
    Get-ChildItem -Path . -Recurse -Name "*.pyc" | Remove-Item -Force
    Get-ChildItem -Path . -Recurse -Name "__pycache__" | Remove-Item -Recurse -Force
    if (Test-Path "build") { Remove-Item -Path "build" -Recurse -Force }
    if (Test-Path "dist") { Remove-Item -Path "dist" -Recurse -Force }
    if (Test-Path "htmlcov") { Remove-Item -Path "htmlcov" -Recurse -Force }
    if (Test-Path ".coverage") { Remove-Item -Path ".coverage" -Force }
    if (Test-Path ".pytest_cache") { Remove-Item -Path ".pytest_cache" -Recurse -Force }
}

function Start-WebUI {
    Write-Host "啟動 Web UI..." -ForegroundColor Green
    python main.py
}

function Start-CLI {
    Write-Host "啟動 CLI 模式..." -ForegroundColor Green
    python main.py --cli
}

function Build-Package {
    Write-Host "建置套件..." -ForegroundColor Yellow
    python -m build
}

# 主要邏輯
switch ($Command.ToLower()) {
    "help" { Show-Help }
    "install" { Install-Base }
    "install-dev" { Install-Dev }
    "test" { Run-Tests }
    "test-unit" { Run-UnitTests }
    "test-int" { Run-IntegrationTests }
    "lint" { Run-Lint }
    "format" { Format-Code }
    "clean" { Clean-Project }
    "run" { Start-WebUI }
    "run-cli" { Start-CLI }
    "build" { Build-Package }
    default { 
        Write-Host "未知命令: $Command" -ForegroundColor Red
        Show-Help 
    }
}
