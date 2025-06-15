#!/usr/bin/env python3
"""
JoJo Trading System - Test Runner Script
測試執行腳本，提供不同的測試執行選項

Usage:
    python run_tests.py --help                    # 顯示幫助
    python run_tests.py --all                     # 執行所有測試
    python run_tests.py --unit                    # 只執行單元測試
    python run_tests.py --integration             # 只執行整合測試
    python run_tests.py --system                  # 只執行系統測試
    python run_tests.py --fast                    # 只執行快速測試
    python run_tests.py --coverage                # 生成覆蓋率報告
    python run_tests.py --performance             # 執行性能測試
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path

# 項目根目錄
PROJECT_ROOT = Path(__file__).parent
REPORTS_DIR = PROJECT_ROOT / "reports"

def ensure_reports_dir():
    """確保報告目錄存在"""
    REPORTS_DIR.mkdir(exist_ok=True)
    (REPORTS_DIR / "coverage").mkdir(exist_ok=True)

def run_command(cmd, description):
    """執行命令並顯示結果"""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}")
    print(f"執行命令: {' '.join(cmd)}")
    print("-" * 60)
    
    try:
        result = subprocess.run(cmd, cwd=PROJECT_ROOT, check=True)
        print(f"\n✅ {description} - 成功完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {description} - 執行失敗 (退出碼: {e.returncode})")
        return False

def run_unit_tests():
    """執行單元測試"""
    cmd = ["python", "-m", "pytest", "tests/unit/", "-v", "--tb=short"]
    return run_command(cmd, "執行單元測試")

def run_integration_tests():
    """執行整合測試"""
    cmd = ["python", "-m", "pytest", "tests/integration/", "-v", "--tb=short"]
    return run_command(cmd, "執行整合測試")

def run_system_tests():
    """執行系統測試"""
    cmd = ["python", "-m", "pytest", "tests/system/", "-v", "--tb=short"]
    return run_command(cmd, "執行系統測試")

def run_fast_tests():
    """執行快速測試"""
    cmd = ["python", "-m", "pytest", "-m", "fast", "-v"]
    return run_command(cmd, "執行快速測試")

def run_slow_tests():
    """執行慢速測試"""
    cmd = ["python", "-m", "pytest", "-m", "slow", "-v"]
    return run_command(cmd, "執行慢速測試")

def run_performance_tests():
    """執行性能測試"""
    cmd = ["python", "-m", "pytest", "-m", "performance", "-v", "--tb=short"]
    return run_command(cmd, "執行性能測試")

def run_all_tests():
    """執行所有測試"""
    cmd = ["python", "-m", "pytest", "tests/", "-v"]
    return run_command(cmd, "執行所有測試")

def run_with_coverage():
    """執行測試並生成覆蓋率報告"""
    cmd = [
        "python", "-m", "pytest", 
        "tests/",
        "--cov=src",
        "--cov-report=html:reports/coverage",
        "--cov-report=term-missing",
        "--cov-report=xml:reports/coverage.xml",
        "-v"
    ]
    success = run_command(cmd, "執行測試並生成覆蓋率報告")
    
    if success:
        coverage_report = REPORTS_DIR / "coverage" / "index.html"
        if coverage_report.exists():
            print(f"\n📊 覆蓋率報告已生成: {coverage_report}")
            print("   在瀏覽器中打開查看詳細覆蓋率信息")
    
    return success

def run_smoke_tests():
    """執行冒煙測試"""
    cmd = ["python", "-m", "pytest", "-m", "smoke", "-v", "--tb=line"]
    return run_command(cmd, "執行冒煙測試")

def lint_code():
    """執行代碼檢查"""
    print(f"\n{'='*60}")
    print("🔍 執行代碼品質檢查")
    print(f"{'='*60}")
    
    # 檢查是否安裝了必要的工具
    tools = {
        "flake8": "代碼風格檢查",
        "black": "代碼格式化檢查", 
        "isort": "導入排序檢查",
        "mypy": "類型檢查"
    }
    
    available_tools = []
    for tool in tools:
        try:
            subprocess.run([tool, "--version"], capture_output=True, check=True)
            available_tools.append(tool)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"⚠️  {tool} 未安裝，跳過 {tools[tool]}")
    
    success = True
    
    # 執行可用的檢查工具
    if "flake8" in available_tools:
        cmd = ["flake8", "src/", "tests/", "--max-line-length=88", "--extend-ignore=E203,W503"]
        success &= run_command(cmd, "Flake8 代碼風格檢查")
    
    if "black" in available_tools:
        cmd = ["black", "--check", "--diff", "src/", "tests/"]
        success &= run_command(cmd, "Black 代碼格式檢查")
    
    if "isort" in available_tools:
        cmd = ["isort", "--check-only", "--diff", "src/", "tests/"]
        success &= run_command(cmd, "isort 導入排序檢查")
    
    if "mypy" in available_tools:
        cmd = ["mypy", "src/"]
        success &= run_command(cmd, "MyPy 類型檢查")
    
    return success

def show_test_summary():
    """顯示測試摘要"""
    print(f"\n{'='*60}")
    print("📈 測試執行摘要")
    print(f"{'='*60}")
    
    # 檢查報告文件
    test_report = REPORTS_DIR / "test_report.html"
    coverage_report = REPORTS_DIR / "coverage" / "index.html"
    
    if test_report.exists():
        print(f"📋 測試報告: {test_report}")
    
    if coverage_report.exists():
        print(f"📊 覆蓋率報告: {coverage_report}")
    
    print("\n💡 建議:")
    print("   - 定期執行完整測試套件")
    print("   - 保持測試覆蓋率在 80% 以上")
    print("   - 修復所有失敗的測試")
    print("   - 為新功能添加相應的測試")

def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description="JoJo Trading System 測試執行器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    # 添加命令行參數
    parser.add_argument("--all", action="store_true", help="執行所有測試")
    parser.add_argument("--unit", action="store_true", help="執行單元測試")
    parser.add_argument("--integration", action="store_true", help="執行整合測試")
    parser.add_argument("--system", action="store_true", help="執行系統測試")
    parser.add_argument("--fast", action="store_true", help="執行快速測試")
    parser.add_argument("--slow", action="store_true", help="執行慢速測試")
    parser.add_argument("--performance", action="store_true", help="執行性能測試")
    parser.add_argument("--smoke", action="store_true", help="執行冒煙測試")
    parser.add_argument("--coverage", action="store_true", help="生成覆蓋率報告")
    parser.add_argument("--lint", action="store_true", help="執行代碼品質檢查")
    parser.add_argument("--ci", action="store_true", help="CI/CD 模式（執行所有檢查）")
    
    args = parser.parse_args()
    
    # 確保報告目錄存在
    ensure_reports_dir()
    
    # 顯示開始信息
    print("🎯 JoJo Trading System - 測試執行器")
    print(f"項目根目錄: {PROJECT_ROOT}")
    
    success = True
    
    # 根據參數執行相應的測試
    if args.ci:
        print("\n🤖 執行 CI/CD 模式測試")
        success &= lint_code()
        success &= run_smoke_tests()
        success &= run_with_coverage()
        
    elif args.lint:
        success &= lint_code()
        
    elif args.coverage:
        success &= run_with_coverage()
        
    elif args.unit:
        success &= run_unit_tests()
        
    elif args.integration:
        success &= run_integration_tests()
        
    elif args.system:
        success &= run_system_tests()
        
    elif args.fast:
        success &= run_fast_tests()
        
    elif args.slow:
        success &= run_slow_tests()
        
    elif args.performance:
        success &= run_performance_tests()
        
    elif args.smoke:
        success &= run_smoke_tests()
        
    elif args.all:
        success &= run_all_tests()
        
    else:
        # 默認執行快速測試
        print("\n💡 未指定測試類型，執行快速測試")
        print("   使用 --help 查看所有選項")
        success &= run_fast_tests()
    
    # 顯示測試摘要
    show_test_summary()
    
    # 根據測試結果設定退出碼
    if success:
        print(f"\n🎉 測試執行完成！")
        sys.exit(0)
    else:
        print(f"\n💥 測試執行失敗！請檢查錯誤並修復。")
        sys.exit(1)

if __name__ == "__main__":
    main()
