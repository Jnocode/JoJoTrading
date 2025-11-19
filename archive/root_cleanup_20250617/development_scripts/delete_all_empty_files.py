#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完全清理空白檔案
刪除專案中所有空白檔案
"""

import os
from pathlib import Path

def delete_all_empty_files():
    """刪除所有空白檔案"""
    
    project_root = Path(".")
    
    # 排除的目錄
    exclude_dirs = {
        ".venv", "venv", "__pycache__", ".git", 
        "node_modules", ".pytest_cache"
    }
    
    print("🔍 掃描所有空白檔案...")
    
    empty_files = []
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
    
    if not empty_files:
        print("✅ 沒有發現空白檔案！")
        return 0
    
    print(f"📊 發現 {len(empty_files)} 個空白檔案")
    
    # 分類顯示
    categories = {}
    for file_path in empty_files:
        path_str = str(file_path).lower()
        
        if "test" in path_str:
            category = "tests"
        elif "docs" in path_str or "documentation" in path_str:
            category = "docs"
        elif "script" in path_str:
            category = "scripts"
        elif "pages" in path_str:
            category = "pages"
        elif "archive" in path_str or "backup" in path_str:
            category = "archive"
        elif "log" in path_str:
            category = "logs"
        elif "cache" in path_str:
            category = "cache"
        else:
            category = "others"
        
        if category not in categories:
            categories[category] = []
        categories[category].append(file_path)
    
    # 顯示分類統計
    for category, files in categories.items():
        print(f"  {category}: {len(files)} 個檔案")
    
    # 開始刪除
    print(f"\n🗑️ 開始刪除所有空白檔案...")
    
    deleted_count = 0
    failed_count = 0
    
    for file_path in empty_files:
        try:
            file_path.unlink()
            print(f"  ✅ 已刪除: {file_path}")
            deleted_count += 1
        except Exception as e:
            print(f"  ❌ 刪除失敗 {file_path}: {e}")
            failed_count += 1
    
    return deleted_count, failed_count

def main():
    """主函數"""
    
    print("🗑️ JoJo Trading 完全清理空白檔案")
    print("=" * 50)
    print("⚠️ 警告：將刪除所有空白檔案，無法復原！")
    
    # 執行刪除
    result = delete_all_empty_files()
    
    if isinstance(result, tuple):
        deleted_count, failed_count = result
        print(f"\n🎉 清理完成！")
        print(f"✅ 成功刪除: {deleted_count} 個檔案")
        if failed_count > 0:
            print(f"❌ 刪除失敗: {failed_count} 個檔案")
    
    # 驗證結果
    print(f"\n🔍 驗證清理結果...")
    remaining_empty = []
    project_root = Path(".")
    exclude_dirs = {".venv", "venv", "__pycache__", ".git", "node_modules", ".pytest_cache"}
    
    for file_path in project_root.rglob("*"):
        if file_path.is_dir():
            continue
        if any(excluded in file_path.parts for excluded in exclude_dirs):
            continue
        if file_path.stat().st_size == 0:
            remaining_empty.append(file_path)
    
    if remaining_empty:
        print(f"⚠️ 仍有 {len(remaining_empty)} 個空白檔案未清理")
        for file_path in remaining_empty[:5]:  # 只顯示前5個
            print(f"  - {file_path}")
    else:
        print("✅ 所有空白檔案已清理完成！")

if __name__ == "__main__":
    main()
