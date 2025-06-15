#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JoJo Trading 功能驗證測試 (重建版)
驗證系統各項功能是否正常運作
"""

import sys
import os
import unittest
from pathlib import Path

# 設置編碼
import io
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加src路徑
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)

class TestJoJoTradingModules(unittest.TestCase):
    """JoJo Trading 模組測試"""
    
    def setUp(self):
        """測試設置"""
        self.src_path = os.path.join(os.path.dirname(__file__), 'src')
        if self.src_path not in sys.path:
            sys.path.insert(0, self.src_path)
    
    def test_main_module_import(self):
        """測試主模組導入"""
        try:
            import jojo_trading
            self.assertTrue(hasattr(jojo_trading, '__version__'))
            print("[OK] 主模組導入成功 (v{})".format(jojo_trading.__version__))
        except ImportError as e:
            self.fail(f"主模組導入失敗: {e}")
    
    def test_config_module(self):
        """測試配置模組"""
        try:
            from jojo_trading.config import get_config_manager
            config_manager = get_config_manager()
            self.assertIsNotNone(config_manager)            print("[OK] 配置模組正常")
        except Exception as e:
            self.fail(f"配置模組測試失敗: {e}")
    
    def test_dcf_ui_module(self):
        """測試DCF UI模組"""
        try:
            from jojo_trading.ui.app import main as dcf_main
            self.assertIsNotNone(dcf_main)
            print("[OK] DCF UI模組正常")
        except Exception as e:
            self.fail(f"DCF UI模組測試失敗: {e}")
    
    def test_trading_ui_module(self):
        """測試交易系統UI模組"""
        try:
            from jojo_trading.trading.trading_ui import TradingSystemUI
            trading_ui = TradingSystemUI()
            self.assertIsNotNone(trading_ui)
            print("[OK] 交易系統UI模組正常")
        except Exception as e:
            self.fail(f"交易系統UI模組測試失敗: {e}")
    
    def test_utils_module(self):
        """測試工具模組"""
        try:
            from jojo_trading.utils import utils
            self.assertIsNotNone(utils)
            print("[OK] 工具模組正常")
        except Exception as e:
            self.fail(f"工具模組測試失敗: {e}")

if __name__ == "__main__":
    print("JoJo Trading 功能驗證測試")
    print("=" * 50)
    
    # 執行測試
    unittest.main(verbosity=2)