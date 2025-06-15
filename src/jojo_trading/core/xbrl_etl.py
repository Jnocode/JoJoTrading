"""
XBRL ETL 模組 - 向後兼容性
"""
# 為了向後兼容，提供基本的 XBRL 處理功能
import os
from pathlib import Path

def parse_xbrl_folder(folder_path):
    """基本的 XBRL 資料夾解析功能"""
    results = []
    folder = Path(folder_path)
    
    if not folder.exists():
        return results
        
    for file in folder.glob("*.xml"):
        # 基本的文件信息
        results.append({
            'file': str(file),
            'size': file.stat().st_size,
            'name': file.name
        })
    
    return results

__all__ = ['parse_xbrl_folder']
