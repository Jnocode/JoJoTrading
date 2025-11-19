#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DCF 頁面清理腳本
統一 DCF 分析頁面，移除重複版本
"""

import os
from pathlib import Path

def cleanup_dcf_pages():
    """清理重複的 DCF 頁面版本"""
    
    project_root = Path(".")
    pages_dir = project_root / "pages"
    enhanced_dir = pages_dir / "enhanced"
    
    # 要刪除的重複檔案列表
    files_to_remove = [
        pages_dir / "📊_DCF分析_unified.py",
        pages_dir / "📊_DCF分析_new.py",
        enhanced_dir / "02_📊_DCF_Calculator.py",  # 空檔案
        enhanced_dir / "🧪_DCF測試.py",  # 簡單測試檔案
    ]
    
    print("🧹 開始清理重複的 DCF 頁面版本...")
    
    for file_path in files_to_remove:
        if file_path.exists():
            try:
                file_path.unlink()
                print(f"✅ 已刪除: {file_path}")
            except Exception as e:
                print(f"❌ 刪除失敗 {file_path}: {e}")
        else:
            print(f"⚠️ 檔案不存在: {file_path}")
    
    # 保留的檔案
    main_dcf_file = pages_dir / "📊_DCF分析.py"
    enhanced_dcf_file = enhanced_dir / "03_📊_DCF_Calculator.py"
    
    print("\n📋 保留的 DCF 相關檔案:")
    if main_dcf_file.exists():
        print(f"✅ 主要版本: {main_dcf_file}")
        print("   - 整合了 AutoDataFetcher 自動資料抓取")
        print("   - 支援個股分析和類股篩選")
        print("   - 使用真實財務數據")
    
    if enhanced_dcf_file.exists():
        print(f"✅ 增強版本 (測試): {enhanced_dcf_file}")
        print("   - 專業級 DCF 計算器")
        print("   - 可用於高級功能測試")
    
    print("\n🎯 統一完成！現在只有一個主要的 DCF 分析頁面")
    print("📍 建議使用: pages/📊_DCF分析.py (已整合真實資料抓取)")

if __name__ == "__main__":
    cleanup_dcf_pages()
