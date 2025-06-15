#!/usr/bin/env python3
"""
JoJo Trading 系統遷移腳本
Migration Script for JoJo Trading System

此腳本用於：
1. 備份原始的 app.py
2. 用重構版本替換原始版本
3. 清理不必要的文件
4. 設置默認配置

使用方法：
python migrate_to_refactored.py
"""

import os
import shutil
import json
import datetime
from pathlib import Path

class JoJoTradingMigration:
    """JoJo Trading 系統遷移管理器"""
    
    def __init__(self, project_root: str = None):
        """初始化遷移管理器"""
        self.project_root = Path(project_root) if project_root else Path(__file__).parent
        self.src_dir = self.project_root / "src" / "jojo_trading"
        self.backup_dir = self.project_root / "archive" / f"migration_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        print(f"🚀 JoJo Trading 系統遷移工具")
        print(f"📁 項目根目錄: {self.project_root}")
        print(f"📁 備份目錄: {self.backup_dir}")
    
    def create_backup_directory(self):
        """創建備份目錄"""
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ 備份目錄已創建: {self.backup_dir}")
    
    def backup_original_app(self):
        """備份原始的 app.py"""
        original_app = self.src_dir / "ui" / "app.py"
        if original_app.exists():
            backup_app = self.backup_dir / "app_original.py"
            shutil.copy2(original_app, backup_app)
            print(f"✅ 原始 app.py 已備份至: {backup_app}")
            return True
        else:
            print(f"⚠️  原始 app.py 不存在: {original_app}")
            return False
    
    def migrate_app_file(self):
        """遷移應用程序文件"""
        refactored_app = self.src_dir / "ui" / "app_refactored.py"
        target_app = self.src_dir / "ui" / "app.py"
        
        if refactored_app.exists():
            # 如果原始app.py存在，先備份
            if target_app.exists():
                self.backup_original_app()
            
            # 複製重構版本
            shutil.copy2(refactored_app, target_app)
            print(f"✅ 重構版本已遷移至: {target_app}")
            
            # 保留重構版本作為參考
            print(f"📝 重構版本仍保留在: {refactored_app}")
            return True
        else:
            print(f"❌ 重構版本不存在: {refactored_app}")
            return False
    
    def setup_default_config(self):
        """設置默認配置"""
        config_dir = self.project_root / "config"
        config_dir.mkdir(exist_ok=True)
        
        default_config_file = config_dir / "default_config.json"
        
        if not default_config_file.exists():
            print(f"⚠️  默認配置文件不存在，請確保已經創建: {default_config_file}")
            return False
        
        # 創建用戶配置目錄
        user_config_dir = self.project_root / "user_configs"
        user_config_dir.mkdir(exist_ok=True)
        
        print(f"✅ 配置系統已設置")
        print(f"   - 默認配置: {default_config_file}")
        print(f"   - 用戶配置目錄: {user_config_dir}")
        return True
    
    def identify_cleanup_candidates(self):
        """識別需要清理的文件"""
        cleanup_candidates = {
            "測試文件": [],
            "報告文件": [],
            "重複應用文件": [],
            "臨時文件": [],
            "快取文件": []
        }
        
        # 掃描根目錄
        for item in self.project_root.iterdir():
            if item.is_file():
                name = item.name.lower()
                
                # 測試文件
                if name.startswith("test_") or name.endswith("_test.py") or "test" in name:
                    cleanup_candidates["測試文件"].append(item)
                
                # 報告文件
                elif name.endswith(".md") and any(keyword in name for keyword in ["report", "完成", "fix", "verification"]):
                    cleanup_candidates["報告文件"].append(item)
                
                # 重複應用文件
                elif name.startswith("main_app") and name != "main_app.py":
                    cleanup_candidates["重複應用文件"].append(item)
                
                # 臨時文件
                elif any(keyword in name for keyword in ["temp", "demo", "simple_", "quick_", "final_"]):
                    cleanup_candidates["臨時文件"].append(item)
                
                # 快取文件
                elif name.endswith((".pyc", ".pyo")) or name.startswith("."):
                    cleanup_candidates["快取文件"].append(item)
        
        return cleanup_candidates
    
    def display_cleanup_plan(self, cleanup_candidates):
        """顯示清理計劃"""
        print(f"\n🧹 文件清理計劃：")
        print("=" * 50)
        
        total_files = 0
        for category, files in cleanup_candidates.items():
            if files:
                print(f"\n📂 {category} ({len(files)} 個文件):")
                for file in files[:5]:  # 只顯示前5個
                    print(f"   - {file.name}")
                if len(files) > 5:
                    print(f"   ... 還有 {len(files) - 5} 個文件")
                total_files += len(files)
        
        print(f"\n📊 總共 {total_files} 個文件待清理")
        return total_files
    
    def create_cleanup_script(self, cleanup_candidates):
        """創建清理腳本"""
        script_content = '''#!/usr/bin/env python3
"""
自動生成的文件清理腳本
Generated File Cleanup Script

注意：運行此腳本前請確保已備份重要文件！
"""

import os
import shutil
from pathlib import Path

def cleanup_files():
    """清理不必要的文件"""
    project_root = Path(__file__).parent
    backup_dir = project_root / "archive" / "cleanup_backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # 要清理的文件列表
    files_to_cleanup = [
'''
        
        for category, files in cleanup_candidates.items():
            if files:
                script_content += f'\n        # {category}\n'
                for file in files:
                    script_content += f'        "{file.name}",\n'
        
        script_content += '''    ]
    
    print(f"🧹 開始清理 {len(files_to_cleanup)} 個文件...")
    
    for filename in files_to_cleanup:
        file_path = project_root / filename
        if file_path.exists():
            # 備份檔案
            backup_path = backup_dir / filename
            shutil.copy2(file_path, backup_path)
            
            # 刪除原檔案
            file_path.unlink()
            print(f"✅ 已清理: {filename}")
        else:
            print(f"⚠️  文件不存在: {filename}")
    
    print(f"✅ 清理完成！備份位於: {backup_dir}")

if __name__ == "__main__":
    cleanup_files()
'''
        
        cleanup_script = self.project_root / "cleanup_unnecessary_files.py"
        cleanup_script.write_text(script_content, encoding='utf-8')
        print(f"✅ 清理腳本已創建: {cleanup_script}")
        return cleanup_script
    
    def create_migration_report(self, success_steps):
        """創建遷移報告"""
        report_content = f"""# JoJo Trading 系統遷移報告
## Migration Report for JoJo Trading System

**遷移時間**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**遷移版本**: 模組化重構版本

## 遷移摘要

### ✅ 已完成步驟：
"""
        
        for step in success_steps:
            report_content += f"- {step}\n"
        
        report_content += f"""
### 📁 目錄結構
```
src/jojo_trading/
├── config/
│   ├── __init__.py
│   ├── config_manager.py
│   └── default_config.json
├── ui/
│   ├── components/
│   │   ├── __init__.py
│   │   ├── individual_dcf.py
│   │   ├── sector_screening.py
│   │   └── common_widgets.py
│   ├── app.py (重構版本)
│   └── app_refactored.py (保留參考)
├── utils/
│   └── utils.py
└── core/ (原有業務邏輯)
```

### 🎯 重構成果
- **代碼行數減少**: 從 2132 行減少到 ~150 行主應用文件
- **模組化設計**: 採用組件化架構
- **配置集中管理**: 統一配置管理系統
- **錯誤處理改善**: 完善的錯誤處理機制
- **調試支持**: 內建調試模式

### 📋 後續建議
1. 測試重構後的應用程序功能
2. 運行清理腳本移除不必要文件
3. 更新文檔和部署腳本
4. 進行性能測試驗證

### 🔗 相關文件
- 備份目錄: `{self.backup_dir}`
- 配置文件: `config/default_config.json`
- 清理腳本: `cleanup_unnecessary_files.py`
"""
        
        report_file = self.project_root / "MIGRATION_REPORT.md"
        report_file.write_text(report_content, encoding='utf-8')
        print(f"✅ 遷移報告已創建: {report_file}")
        return report_file
    
    def run_migration(self):
        """執行完整遷移流程"""
        print(f"\n🚀 開始 JoJo Trading 系統遷移...")
        print("=" * 50)
        
        success_steps = []
        
        # 1. 創建備份目錄
        try:
            self.create_backup_directory()
            success_steps.append("✅ 創建備份目錄")
        except Exception as e:
            print(f"❌ 創建備份目錄失敗: {e}")
            return False
        
        # 2. 遷移應用文件
        try:
            if self.migrate_app_file():
                success_steps.append("✅ 遷移主應用文件 (app.py)")
        except Exception as e:
            print(f"❌ 遷移應用文件失敗: {e}")
        
        # 3. 設置配置
        try:
            if self.setup_default_config():
                success_steps.append("✅ 設置默認配置")
        except Exception as e:
            print(f"❌ 設置配置失敗: {e}")
        
        # 4. 分析清理候選文件
        try:
            cleanup_candidates = self.identify_cleanup_candidates()
            total_cleanup_files = self.display_cleanup_plan(cleanup_candidates)
            
            if total_cleanup_files > 0:
                cleanup_script = self.create_cleanup_script(cleanup_candidates)
                success_steps.append(f"✅ 識別 {total_cleanup_files} 個待清理文件並創建清理腳本")
        except Exception as e:
            print(f"❌ 文件清理分析失敗: {e}")
        
        # 5. 創建遷移報告
        try:
            self.create_migration_report(success_steps)
            success_steps.append("✅ 創建遷移報告")
        except Exception as e:
            print(f"❌ 創建遷移報告失敗: {e}")
        
        # 總結
        print(f"\n🎉 遷移完成！")
        print(f"✅ 成功完成 {len(success_steps)} 個步驟")
        print(f"\n📋 下一步建議：")
        print(f"1. 測試重構後的應用: streamlit run src/jojo_trading/ui/app.py")
        print(f"2. 運行清理腳本: python cleanup_unnecessary_files.py")
        print(f"3. 查看遷移報告: MIGRATION_REPORT.md")
        
        return True


def main():
    """主函數"""
    migration = JoJoTradingMigration()
    migration.run_migration()


if __name__ == "__main__":
    main()
