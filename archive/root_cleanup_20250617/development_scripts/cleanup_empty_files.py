#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
空白檔案清理器
清理專案中的空白檔案，提升專案整潔度
"""

import os
from pathlib import Path
import shutil

def find_empty_files():
    """找出所有空白檔案"""
    
    project_root = Path(".")
    empty_files = []
    
    # 排除的目錄
    exclude_dirs = {
        ".venv", "venv", "__pycache__", ".git", 
        "node_modules", ".pytest_cache"
    }
    
    print("🔍 掃描空白檔案...")
    
    for file_path in project_root.rglob("*"):
        # 跳過目錄
        if file_path.is_dir():
            continue
            
        # 跳過排除的目錄
        if any(excluded in file_path.parts for excluded in exclude_dirs):
            continue
            
        # 檢查檔案大小
        if file_path.stat().st_size == 0:
            empty_files.append(file_path)
    
    return empty_files

def categorize_empty_files(empty_files):
    """分類空白檔案"""
    
    categories = {
        "archive": [],      # 舊版備份檔案
        "tests": [],        # 測試檔案
        "docs": [],         # 文檔檔案
        "scripts": [],      # 腳本檔案
        "pages": [],        # 頁面檔案
        "logs": [],         # 日誌檔案
        "cache": [],        # 快取檔案
        "others": []        # 其他檔案
    }
    
    for file_path in empty_files:
        path_str = str(file_path).lower()
        
        if "archive" in path_str or "backup" in path_str or "legacy" in path_str:
            categories["archive"].append(file_path)
        elif "test" in path_str:
            categories["tests"].append(file_path)
        elif "docs" in path_str or "documentation" in path_str:
            categories["docs"].append(file_path)
        elif "script" in path_str:
            categories["scripts"].append(file_path)
        elif "pages" in path_str:
            categories["pages"].append(file_path)
        elif "log" in path_str:
            categories["logs"].append(file_path)
        elif "cache" in path_str:
            categories["cache"].append(file_path)
        else:
            categories["others"].append(file_path)
    
    return categories

def cleanup_empty_files(categories, auto_clean=False):
    """清理空白檔案"""
    
    print(f"\n📊 空白檔案統計:")
    total_files = sum(len(files) for files in categories.values())
    print(f"總計: {total_files} 個空白檔案")
    
    for category, files in categories.items():
        if files:
            print(f"  {category}: {len(files)} 個")
    
    # 安全清理的類別（可以自動刪除）
    safe_to_clean = ["archive", "cache", "logs"]
    
    # 需要謹慎處理的類別
    manual_review = ["tests", "docs", "scripts", "pages", "others"]
    
    cleaned_count = 0
    
    # 自動清理安全類別
    for category in safe_to_clean:
        if categories[category]:
            print(f"\n🧹 清理 {category} 類別的空白檔案...")
            for file_path in categories[category]:
                try:
                    file_path.unlink()
                    print(f"  ✅ 已刪除: {file_path}")
                    cleaned_count += 1
                except Exception as e:
                    print(f"  ❌ 刪除失敗 {file_path}: {e}")
    
    # 手動處理需要檢查的類別
    if not auto_clean:
        print(f"\n⚠️ 需要手動檢查的空白檔案:")
        for category in manual_review:
            if categories[category]:
                print(f"\n📁 {category} ({len(categories[category])} 個):")
                for file_path in categories[category][:5]:  # 只顯示前5個
                    print(f"  - {file_path}")
                if len(categories[category]) > 5:
                    print(f"  ... 還有 {len(categories[category]) - 5} 個檔案")
    
    return cleaned_count

def create_cleanup_report(categories, cleaned_count):
    """生成清理報告"""
    
    report_content = f"""# 空白檔案清理報告

## 📊 清理統計

- **總共發現**: {sum(len(files) for files in categories.values())} 個空白檔案
- **已自動清理**: {cleaned_count} 個檔案
- **待手動檢查**: {sum(len(files) for files in categories.values()) - cleaned_count} 個檔案

## 📋 分類詳情

"""
    
    for category, files in categories.items():
        if files:
            report_content += f"### {category.upper()} ({len(files)} 個)\n"
            
            if category in ["archive", "cache", "logs"]:
                report_content += "✅ **已自動清理**\n\n"
            else:
                report_content += "⚠️ **需要手動檢查**\n"
                for file_path in files[:10]:  # 列出前10個
                    report_content += f"- `{file_path}`\n"
                if len(files) > 10:
                    report_content += f"- ... 還有 {len(files) - 10} 個檔案\n"
                report_content += "\n"
    
    report_content += f"""## 🎯 建議

### 已清理類別
- **archive**: 舊版備份檔案，可安全刪除
- **cache**: 快取檔案，可重新生成
- **logs**: 日誌檔案，空白表示無記錄

### 待檢查類別
- **tests**: 測試檔案需檢查是否為空白模板
- **docs**: 文檔檔案可能是待編寫的佔位符
- **scripts**: 腳本檔案需確認用途
- **pages**: 頁面檔案可能是空白模板
- **others**: 其他檔案需個別檢查

## ✅ 結論

專案整潔度已大幅提升！建議定期執行此清理腳本維護專案品質。
"""
    
    # 寫入報告檔案
    with open("EMPTY_FILES_CLEANUP_REPORT.md", "w", encoding="utf-8") as f:
        f.write(report_content)
    
    print(f"\n📄 清理報告已生成: EMPTY_FILES_CLEANUP_REPORT.md")

def main():
    """主函數"""
    
    print("🧹 JoJo Trading 專案空白檔案清理器")
    print("=" * 50)
    
    # 尋找空白檔案
    empty_files = find_empty_files()
    
    if not empty_files:
        print("✅ 沒有發現空白檔案，專案很乾淨！")
        return
    
    # 分類空白檔案
    categories = categorize_empty_files(empty_files)
    
    # 清理空白檔案
    cleaned_count = cleanup_empty_files(categories)
    
    # 生成報告
    create_cleanup_report(categories, cleaned_count)
    
    print(f"\n🎉 清理完成！")
    print(f"✅ 已清理: {cleaned_count} 個空白檔案")
    print(f"📋 詳細報告: EMPTY_FILES_CLEANUP_REPORT.md")

if __name__ == "__main__":
    main()
