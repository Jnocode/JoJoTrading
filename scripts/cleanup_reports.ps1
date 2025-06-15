# JoJo Trading 文檔清理腳本
# 執行前請先備份！

# 1. 創建歸檔目錄
New-Item -ItemType Directory -Path "docs\archive\reports_2025_backup" -Force

# 2. 移動可保留的文件到適當位置

# 轉移到 user_guides
Move-Item "docs\reports\USER_GUIDE.md" "docs\user_guides\" -Force
Move-Item "docs\reports\USER_GUIDE_PHASE1.md" "docs\user_guides\" -Force  
Move-Item "docs\reports\TAIWAN_PRESET_USAGE_GUIDE.md" "docs\user_guides\" -Force
Move-Item "docs\reports\QUICK_START.md" "docs\user_guides\" -Force
Move-Item "docs\reports\TESTING_GUIDE.md" "docs\user_guides\" -Force
Move-Item "docs\reports\GROWTH_OPTIMIZATION_README.md" "docs\user_guides\" -Force

# 轉移到 technical
Move-Item "docs\reports\STREAMLIT_ARCH_DIAGRAM.md" "docs\technical\" -Force
Move-Item "docs\reports\DCF_NEGATIVE_VALUATION_ANALYSIS.md" "docs\technical\" -Force
Move-Item "docs\reports\ANOMALY_DETECTION_IMPLEMENTATION_REPORT.md" "docs\technical\" -Force
Move-Item "docs\reports\CONFIGURATION_SYSTEM_COMPLETION_REPORT.md" "docs\technical\" -Force
Move-Item "docs\reports\DEV_FLOW_AND_REQUIREMENTS.md" "docs\technical\" -Force
Move-Item "docs\reports\DEVELOPER_LOG.md" "docs\technical\" -Force

# 3. 歸檔重要歷史文檔
Move-Item "docs\reports\GROWTH_OPTIMIZATION_COMPLETION_REPORT.md" "docs\archive\reports_2025_backup\" -Force
Move-Item "docs\reports\TAIWAN_PRESET_COMPLETION_REPORT.md" "docs\archive\reports_2025_backup\" -Force
Move-Item "docs\reports\TAIWAN_PRESET_CUSTOMIZATION_COMPLETION_REPORT.md" "docs\archive\reports_2025_backup\" -Force
Move-Item "docs\reports\DCF_OPTIMIZATION_*" "docs\archive\reports_2025_backup\" -Force
Move-Item "docs\reports\PROJECT_ORGANIZATION_*" "docs\archive\reports_2025_backup\" -Force

# 4. 刪除已完全整合的文件
$filesToDelete = @(
    "docs\reports\PHASE1_COMPLETION_REPORT.md",
    "docs\reports\PHASE1_FINAL_SUCCESS_REPORT.md",
    "docs\reports\PHASE1_VALIDATION_REPORT.md",
    "docs\reports\FINAL_SUCCESS_REPORT.md", 
    "docs\reports\FINAL_SUCCESS_REPORT_COMPLETE.md",
    "docs\reports\FINAL_PROJECT_COMPLETION_REPORT.md",
    "docs\reports\FINAL_PROJECT_COMPLETION_REPORT_UPDATED.md",
    "docs\reports\DCF_FIX_COMPLETION_REPORT.md",
    "docs\reports\DCF_FIX_VERIFICATION_REPORT.md",
    "docs\reports\DEBUG_REPORT_20250605.md",
    "docs\reports\DATA_HANDLER_BUG_FIX_REPORT.md",
    "docs\reports\DCF_PARAMETER_CONFLICT_FIX_REPORT.md",
    "docs\reports\BUG_FIX_PROGRESS_REPORT.md",
    "docs\reports\CLEANUP_COMPLETION_REPORT.md",
    "docs\reports\ADVANCED_CLEANUP_COMPLETION_REPORT.md",
    "docs\reports\PROJECT_CLEANUP_COMPLETION_REPORT.md",
    "docs\reports\PROJECT_RESTRUCTURE_COMPLETE.md",
    "docs\reports\FINAL_PROJECT_RESTRUCTURE_SUMMARY.md",
    "docs\reports\FINAL_RESTRUCTURE_COMPLETION_SUMMARY.md",
    "docs\reports\DOCUMENTATION_CLEANUP_SUMMARY.md",
    "docs\reports\DEPLOYMENT_GUIDE.md",
    "docs\reports\DEPLOY_TO_GITHUB.md",
    "docs\reports\GITHUB_DEPLOY_GUIDE.md",
    "docs\reports\GITHUB_PUSH_GUIDE.md",
    "docs\reports\FINAL_DEPLOY_STEPS.md",
    "docs\reports\STARTUP_GUIDE.md",
    "docs\reports\MANUAL_STARTUP_GUIDE.md",
    "docs\reports\SYSTEM_STARTUP_GUIDE.md",
    "docs\reports\STARTUP_SCRIPTS_COMPARISON_REPORT.md",
    "docs\reports\STARTUP_STATUS_REPORT.md",
    "docs\reports\SYSTEM_COMPLETION_REPORT.md",
    "docs\reports\SYSTEM_STATUS_FINAL.md",
    "docs\reports\SYSTEM_VERIFICATION_COMPLETE.md",
    "docs\reports\FINAL_PROJECT_STATUS_REPORT.md",
    "docs\reports\PROJECT_STATUS_FINAL_SUMMARY.md"
)

foreach ($file in $filesToDelete) {
    if (Test-Path $file) {
        Remove-Item $file -Force
        Write-Host "已刪除: $file"
    }
}

# 5. 刪除明顯錯誤的文件
Remove-Item "docs\reports\pacedev_projectswebjojo_trading; git add DEPLOY_TO_GITHUB.md" -Force -ErrorAction SilentlyContinue

Write-Host "文檔清理完成！"
Write-Host "- 有用文檔已轉移到 user_guides 和 technical"
Write-Item "- 歷史文檔已歸檔到 archive/reports_2025_backup"  
Write-Host "- 已整合文檔已安全刪除"
