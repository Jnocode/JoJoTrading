"""
JoJo Trading 統一測試模組管理器
Unified Test Module Manager

提供完整的測試套件管理、執行和報告功能
"""

import os
import sys
import subprocess
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import json


class TestCategory:
    """測試類別定義"""
    UNIT = "unit"                    # 單元測試
    INTEGRATION = "integration"      # 整合測試
    SYSTEM = "system"               # 系統測試
    PERFORMANCE = "performance"      # 性能測試
    E2E = "e2e"                     # 端到端測試
    SMOKE = "smoke"                 # 煙霧測試
    REGRESSION = "regression"        # 回歸測試


class TestSuite:
    """測試套件定義"""
    QUICK = "quick"                 # 快速測試 (< 30秒)
    STANDARD = "standard"           # 標準測試 (< 5分鐘)
    FULL = "full"                   # 完整測試 (< 30分鐘)
    NIGHTLY = "nightly"            # 夜間測試 (無時間限制)


class UnifiedTestManager:
    """統一測試管理器"""    def __init__(self, project_root: Optional[str] = None):
        """初始化測試管理器"""
        self.project_root = Path(project_root) if project_root else Path(__file__).parent.parent
        self.tests_dir = self.project_root / "tests"
        self.reports_dir = self.tests_dir / "reports"
        self.reports_dir.mkdir(exist_ok=True)
        
        # 測試配置
        self.test_modules = self._discover_test_modules()
        self.test_suites = self._define_test_suites()
        
    def _discover_test_modules(self) -> Dict[str, List[str]]:
        """發現所有測試模組"""
        modules = {
            TestCategory.UNIT: [],
            TestCategory.INTEGRATION: [],
            TestCategory.SYSTEM: [],
            TestCategory.PERFORMANCE: [],
            TestCategory.E2E: [],
            TestCategory.SMOKE: [],
            TestCategory.REGRESSION: []
        }
        
        # 掃描 tests 目錄
        if self.tests_dir.exists():
            for category in modules.keys():
                category_dir = self.tests_dir / category
                if category_dir.exists():
                    for test_file in category_dir.glob("test_*.py"):
                        modules[category].append(str(test_file.relative_to(self.project_root)))
        
        # 掃描根目錄的測試文件
        root_tests = list(self.project_root.glob("test_*.py"))
        root_tests.extend(list(self.project_root.glob("*_test.py")))
        root_tests.extend(list(self.project_root.glob("verify_*.py")))
        
        for test_file in root_tests:
            # 根據文件名判斷類別
            name = test_file.name.lower()
            if "performance" in name or "perf" in name:
                modules[TestCategory.PERFORMANCE].append(str(test_file.relative_to(self.project_root)))
            elif "integration" in name or "system" in name:
                modules[TestCategory.INTEGRATION].append(str(test_file.relative_to(self.project_root)))
            elif "verify" in name or "basic" in name:
                modules[TestCategory.SMOKE].append(str(test_file.relative_to(self.project_root)))
            else:
                modules[TestCategory.UNIT].append(str(test_file.relative_to(self.project_root)))
        
        return modules
    
    def _define_test_suites(self) -> Dict[str, Dict[str, List[str]]]:
        """定義測試套件"""
        return {
            TestSuite.QUICK: {
                "description": "快速測試套件 - 基本功能驗證 (< 30秒)",
                "categories": [TestCategory.SMOKE, TestCategory.UNIT]
            },
            TestSuite.STANDARD: {
                "description": "標準測試套件 - 核心功能完整測試 (< 5分鐘)",
                "categories": [TestCategory.SMOKE, TestCategory.UNIT, TestCategory.INTEGRATION]
            },
            TestSuite.FULL: {
                "description": "完整測試套件 - 所有功能測試 (< 30分鐘)",
                "categories": [TestCategory.SMOKE, TestCategory.UNIT, TestCategory.INTEGRATION, 
                             TestCategory.SYSTEM, TestCategory.E2E]
            },
            TestSuite.NIGHTLY: {
                "description": "夜間測試套件 - 包含性能測試 (無時間限制)",
                "categories": list(TestCategory.__dict__.values())
            }
        }
    
    def list_tests(self, category: str = None, suite: str = None) -> None:
        """列出測試"""
        print("🔍 JoJo Trading 測試模組清單")
        print("=" * 60)
        
        if suite:
            self._list_suite_tests(suite)
        elif category:
            self._list_category_tests(category)
        else:
            self._list_all_tests()
    
    def _list_suite_tests(self, suite: str) -> None:
        """列出測試套件"""
        if suite not in self.test_suites:
            print(f"❌ 未知的測試套件: {suite}")
            return
        
        suite_info = self.test_suites[suite]
        print(f"📋 測試套件: {suite}")
        print(f"描述: {suite_info['description']}")
        print()
        
        for category in suite_info['categories']:
            if category in self.test_modules and self.test_modules[category]:
                print(f"📂 {category.upper()}:")
                for test in self.test_modules[category]:
                    print(f"   ✓ {test}")
                print()
    
    def _list_category_tests(self, category: str) -> None:
        """列出分類測試"""
        if category not in self.test_modules:
            print(f"❌ 未知的測試分類: {category}")
            return
        
        print(f"📂 測試分類: {category.upper()}")
        tests = self.test_modules[category]
        if tests:
            for test in tests:
                print(f"   ✓ {test}")
        else:
            print("   (無測試文件)")
        print()
    
    def _list_all_tests(self) -> None:
        """列出所有測試"""
        total_tests = 0
        for category, tests in self.test_modules.items():
            if tests:
                print(f"📂 {category.upper()} ({len(tests)} 個測試):")
                for test in tests:
                    print(f"   ✓ {test}")
                total_tests += len(tests)
                print()
        
        print(f"📊 總計: {total_tests} 個測試文件")
        print()
        
        # 顯示測試套件
        print("🎯 可用測試套件:")
        for suite, info in self.test_suites.items():
            print(f"   {suite}: {info['description']}")
    
    def run_tests(self, 
                  suite: str = None, 
                  category: str = None, 
                  test_file: str = None,
                  verbose: bool = False,
                  generate_report: bool = True) -> Dict[str, Any]:
        """執行測試"""
        
        start_time = time.time()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        print(f"🚀 開始執行測試 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # 確定要執行的測試
        test_files = []
        if test_file:
            test_files = [test_file]
        elif suite:
            test_files = self._get_suite_tests(suite)
        elif category:
            test_files = self.test_modules.get(category, [])
        else:
            # 預設執行快速測試
            test_files = self._get_suite_tests(TestSuite.QUICK)
        
        if not test_files:
            print("❌ 沒有找到要執行的測試")
            return {"status": "failed", "reason": "no_tests_found"}
        
        print(f"📋 將執行 {len(test_files)} 個測試文件")
        if verbose:
            for test in test_files:
                print(f"   ✓ {test}")
        print()
        
        # 執行測試
        results = []
        passed = 0
        failed = 0
        
        for test_file in test_files:
            print(f"🔍 執行: {test_file}")
            result = self._run_single_test(test_file, verbose)
            results.append(result)
            
            if result["status"] == "passed":
                passed += 1
                print(f"   ✅ 通過 ({result['duration']:.2f}s)")
            else:
                failed += 1
                print(f"   ❌ 失敗 ({result['duration']:.2f}s)")
                if not verbose and result.get("error"):
                    print(f"      錯誤: {result['error'][:100]}...")
            print()
        
        # 測試總結
        total_time = time.time() - start_time
        summary = {
            "timestamp": timestamp,
            "suite": suite,
            "category": category,
            "total_tests": len(test_files),
            "passed": passed,
            "failed": failed,
            "duration": total_time,
            "results": results
        }
        
        self._print_summary(summary)
        
        # 生成報告
        if generate_report:
            report_file = self._generate_report(summary, timestamp)
            print(f"📄 測試報告已生成: {report_file}")
        
        return summary
    
    def _get_suite_tests(self, suite: str) -> List[str]:
        """獲取測試套件的所有測試"""
        if suite not in self.test_suites:
            return []
        
        test_files = []
        for category in self.test_suites[suite]["categories"]:
            test_files.extend(self.test_modules.get(category, []))
        
        return test_files
    
    def _run_single_test(self, test_file: str, verbose: bool = False) -> Dict[str, Any]:
        """執行單個測試"""
        start_time = time.time()
        
        try:
            # 構建命令
            test_path = self.project_root / test_file
            if not test_path.exists():
                return {
                    "test_file": test_file,
                    "status": "failed",
                    "error": f"測試文件不存在: {test_path}",
                    "duration": 0
                }
            
            # 執行測試
            result = subprocess.run(
                [sys.executable, str(test_path)],
                capture_output=True,
                text=True,
                cwd=str(self.project_root),
                timeout=300  # 5分鐘超時
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                return {
                    "test_file": test_file,
                    "status": "passed",
                    "output": result.stdout if verbose else "",
                    "duration": duration
                }
            else:
                return {
                    "test_file": test_file,
                    "status": "failed",
                    "error": result.stderr or result.stdout,
                    "output": result.stdout if verbose else "",
                    "duration": duration
                }
                
        except subprocess.TimeoutExpired:
            return {
                "test_file": test_file,
                "status": "failed",
                "error": "測試執行超時 (5分鐘)",
                "duration": time.time() - start_time
            }
        except Exception as e:
            return {
                "test_file": test_file,
                "status": "failed",
                "error": f"執行錯誤: {str(e)}",
                "duration": time.time() - start_time
            }
    
    def _print_summary(self, summary: Dict[str, Any]) -> None:
        """打印測試總結"""
        print("=" * 60)
        print("📊 測試執行總結")
        print("=" * 60)
        
        total = summary["total_tests"]
        passed = summary["passed"]
        failed = summary["failed"]
        duration = summary["duration"]
        
        print(f"📋 總測試數: {total}")
        print(f"✅ 通過: {passed} ({passed/total*100:.1f}%)")
        print(f"❌ 失敗: {failed} ({failed/total*100:.1f}%)")
        print(f"⏱️  總時間: {duration:.2f} 秒")
        
        if failed == 0:
            print("\n🎉 所有測試都通過了！")
        else:
            print(f"\n⚠️  有 {failed} 個測試失敗，請檢查錯誤信息")
            
        print("=" * 60)
    
    def _generate_report(self, summary: Dict[str, Any], timestamp: str) -> str:
        """生成測試報告"""
        report_file = self.reports_dir / f"test_report_{timestamp}.json"
        
        # 生成詳細報告
        report = {
            "metadata": {
                "timestamp": timestamp,
                "project": "JoJo Trading",
                "test_manager_version": "1.0.0"
            },
            "summary": summary,
            "environment": {
                "python_version": sys.version,
                "platform": os.name,
                "working_directory": str(self.project_root)
            }
        }
        
        # 保存 JSON 報告
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # 生成 HTML 報告
        html_file = self.reports_dir / f"test_report_{timestamp}.html"
        self._generate_html_report(report, html_file)
        
        return str(report_file)
    
    def _generate_html_report(self, report: Dict[str, Any], html_file: Path) -> None:
        """生成 HTML 測試報告"""
        summary = report["summary"]
        
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>JoJo Trading 測試報告 - {summary['timestamp']}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .metric {{ background: #ecf0f1; padding: 20px; border-radius: 8px; text-align: center; }}
        .metric.passed {{ background: #d5edda; border-left: 4px solid #28a745; }}
        .metric.failed {{ background: #f8d7da; border-left: 4px solid #dc3545; }}
        .results {{ margin-top: 30px; }}
        .test-item {{ margin: 10px 0; padding: 15px; border-radius: 5px; }}
        .test-item.passed {{ background: #d5edda; }}
        .test-item.failed {{ background: #f8d7da; }}
        .error {{ margin-top: 10px; font-family: monospace; background: #f8f9fa; padding: 10px; border-radius: 3px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 JoJo Trading 測試報告</h1>
        <p><strong>生成時間:</strong> {summary['timestamp']}</p>
        
        <div class="summary">
            <div class="metric">
                <h3>總測試數</h3>
                <div style="font-size: 2em; font-weight: bold;">{summary['total_tests']}</div>
            </div>
            <div class="metric passed">
                <h3>通過測試</h3>
                <div style="font-size: 2em; font-weight: bold;">{summary['passed']}</div>
            </div>
            <div class="metric failed">
                <h3>失敗測試</h3>
                <div style="font-size: 2em; font-weight: bold;">{summary['failed']}</div>
            </div>
            <div class="metric">
                <h3>執行時間</h3>
                <div style="font-size: 1.5em; font-weight: bold;">{summary['duration']:.2f}s</div>
            </div>
        </div>
        
        <div class="results">
            <h2>詳細結果</h2>
        """
        
        for result in summary['results']:
            status_class = result['status']
            status_icon = "✅" if result['status'] == 'passed' else "❌"
            
            html_content += f"""
            <div class="test-item {status_class}">
                <strong>{status_icon} {result['test_file']}</strong>
                <span style="float: right;">({result['duration']:.2f}s)</span>
                """
            
            if result.get('error'):
                html_content += f'<div class="error">{result["error"]}</div>'
                
            html_content += "</div>"
        
        html_content += """
        </div>
    </div>
</body>
</html>
        """
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def clean_old_reports(self, days: int = 30) -> None:
        """清理舊的測試報告"""
        cutoff_time = time.time() - (days * 24 * 60 * 60)
        
        removed_count = 0
        for report_file in self.reports_dir.glob("test_report_*"):
            if report_file.stat().st_mtime < cutoff_time:
                report_file.unlink()
                removed_count += 1
        
        print(f"🗑️  清理了 {removed_count} 個超過 {days} 天的舊報告")


def main():
    """主要執行函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description="JoJo Trading 統一測試管理器")
    parser.add_argument("--list", action="store_true", help="列出所有測試")
    parser.add_argument("--suite", type=str, help="執行指定測試套件")
    parser.add_argument("--category", type=str, help="執行指定測試分類")
    parser.add_argument("--test", type=str, help="執行指定測試文件")
    parser.add_argument("--verbose", "-v", action="store_true", help="詳細輸出")
    parser.add_argument("--no-report", action="store_true", help="不生成測試報告")
    parser.add_argument("--clean", type=int, help="清理N天前的舊報告")
    
    args = parser.parse_args()
    
    # 創建測試管理器
    manager = UnifiedTestManager()
    
    if args.clean:
        manager.clean_old_reports(args.clean)
        return
    
    if args.list:
        manager.list_tests(args.category, args.suite)
        return
    
    # 執行測試
    result = manager.run_tests(
        suite=args.suite,
        category=args.category,
        test_file=args.test,
        verbose=args.verbose,
        generate_report=not args.no_report
    )
    
    # 返回適當的退出碼
    sys.exit(0 if result["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
