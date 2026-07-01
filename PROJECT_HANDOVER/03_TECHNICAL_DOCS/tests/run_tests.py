#!/usr/bin/env python3
"""
JoJoTrading 測試運行腳本
"""

import sys
import subprocess
import os


def run_category_tests(category):
    """運行特定類別的測試"""
    print(f"🚀 運行 {category} 測試...")

    test_dir = os.path.join(os.path.dirname(__file__), category)
    if not os.path.exists(test_dir):
        print(f"❌ 測試目錄不存在: {test_dir}")
        return False

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", test_dir, "-v"],
            cwd=os.path.dirname(__file__),
        )
        return result.returncode == 0
    except Exception as e:
        print(f"❌ 測試執行錯誤: {e}")
        return False


def main():
    """主函數"""
    import argparse

    parser = argparse.ArgumentParser(description="JoJoTrading 測試運行器")
    parser.add_argument(
        "category",
        nargs="?",
        choices=["dcf", "growth", "integration", "data", "performance", "all"],
        default="all",
        help="要運行的測試類別",
    )

    args = parser.parse_args()

    if args.category == "all":
        categories = ["dcf", "growth", "integration", "data", "performance"]
        success_count = 0
        for category in categories:
            if run_category_tests(category):
                success_count += 1

        print(f"\n📊 測試完成: {success_count}/{len(categories)} 類別通過")
    else:
        success = run_category_tests(args.category)
        print(f"\n📊 {args.category} 測試 {'✅ 通過' if success else '❌ 失敗'}")


if __name__ == "__main__":
    main()
