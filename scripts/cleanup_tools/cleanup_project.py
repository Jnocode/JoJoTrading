#!/usr/bin/env python3
"""
JoJo Trading 項目清理腳本
Project Cleanup Script for JoJo Trading

此腳本將清理根目錄中的冗余文件，包括：
- 測試文件
- 報告文件  
- 重複的應用程序版本
- 臨時文件
- 舊的修復腳本

運行前會自動備份所有待刪除的文件。
"""

import os
import shutil
import datetime
from pathlib import Path

def main():
    """主清理函數"""
    project_root = Path(__file__).parent
    backup_dir = project_root / "archive" / f"cleanup_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    print("🧹 JoJo Trading 項目清理工具")
    print("=" * 50)
    print(f"📁 項目根目錄: {project_root}")
    print(f"📁 備份目錄: {backup_dir}")
    
    # 定義要清理的文件類別
    cleanup_files = {
        "測試文件": [
            "test_app_status.py",
            "test_dcf_completion.py", 
            "test_dcf_fix.py",
            "test_final_solution.py",
            "test_fixed_navigation.py",
            "test_import.py",
            "test_industries.py",
            "test_monitoring.py",
            "test_navigation_final.py",
            "test_navigation_fixed.py",
            "test_navigation_live.py",
            "test_navigation_simple.py",
            "test_output.txt",
            "test_page_navigation.py",
            "test_sector_screening.py",
            "test_state_machine.py",
            "test_system.py",
            "test_trading_ui.py",
            "functionality_test.py",
            "monitor_integration_test.py",
            "optimized_performance_test.py",
            "performance_test.py",
            "quick_health_check.py",
            "quick_monitor_test.py",
            "simple_dcf_app.py",
            "simple_function_test.py", 
            "simple_navigation_test.py",
            "simple_performance_test.py",
            "simple_test.py",
            "system_test.py"
        ],
        
        "報告文件": [
            "DCF_FIX_COMPLETION_REPORT.md",
            "DCF_SECTOR_SCREENING_COMPLETION_REPORT.md",
            "FINAL_RESOLUTION_REPORT.md",
            "IMPORT_FIX_REPORT.md",
            "NAVIGATION_FINAL_FIX_REPORT.md",
            "NAVIGATION_FIX_COMPLETE.md",
            "NAVIGATION_TEST_REPORT.md",
            "SOLUTION_SUMMARY.md",
            "SYSTEM_COMPREHENSIVE_ANALYSIS.md",
            "SYSTEM_FIX_REPORT.md",
            "SYSTEM_REFACTORING_COMPLETE.md",
            "SYSTEM_VERIFICATION_REPORT.md"
        ],
        
        "重複應用文件": [
            "main_app_fixed.py",
            "main_app_fixed_v2.py",
            "main_app_v3.py"
        ],
        
        "修復和臨時腳本": [
            "demo_output.txt",
            "demo_system.py",
            "final_dcf_verification.py",
            "final_system_check.py",
            "final_system_validation.py",
            "final_verification.py",
            "fix_comprehensive.py",
            "fix_indentation.py", 
            "fix_indentation_issue.py",
            "navigation_fix_verification.py",
            "performance_optimizer.py"
        ]
    }
    
    total_cleaned = 0
    
    # 執行清理
    for category, files in cleanup_files.items():
        print(f"\n📂 清理 {category}...")
        category_cleaned = 0
        
        for filename in files:
            file_path = project_root / filename
            if file_path.exists():
                # 備份文件
                backup_path = backup_dir / filename
                try:
                    shutil.copy2(file_path, backup_path)
                    # 刪除原文件
                    file_path.unlink()
                    print(f"   ✅ {filename}")
                    category_cleaned += 1
                    total_cleaned += 1
                except Exception as e:
                    print(f"   ❌ {filename} - 錯誤: {e}")
            else:
                print(f"   ⚠️  {filename} - 文件不存在")
        
        print(f"   📊 {category}: 清理了 {category_cleaned} 個文件")
    
    # 清理總結
    print(f"\n🎉 清理完成！")
    print(f"✅ 總共清理了 {total_cleaned} 個文件")
    print(f"📁 備份位置: {backup_dir}")
    
    # 顯示清理後的根目錄狀態
    print(f"\n📋 清理後的根目錄主要文件:")
    important_files = [
        ".env", ".gitignore", "pyproject.toml", "requirements.txt", 
        "setup.py", "README.md", "main.py", "main_app.py", "start_app.py"
    ]
    
    for filename in important_files:
        file_path = project_root / filename
        if file_path.exists():
            print(f"   ✅ {filename}")
        else:
            print(f"   ⚠️  {filename} - 缺失")
    
    print(f"\n📁 保留的重要目錄:")
    important_dirs = ["src", "config", "data", "cache", "export", "docs", "tests", "requirements"]
    for dirname in important_dirs:
        dir_path = project_root / dirname
        if dir_path.exists():
            print(f"   ✅ {dirname}/")
    
    print(f"\n🚀 下一步建議:")
    print(f"1. 測試重構後的應用: streamlit run src/jojo_trading/ui/app.py")
    print(f"2. 檢查配置是否正確: python -c 'from src.jojo_trading.config import get_config_manager; print(get_config_manager())'")
    print(f"3. 查看項目結構: tree src/ 或 ls -la src/")
    
    return total_cleaned

if __name__ == "__main__":
    main()
