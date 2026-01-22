# -*- coding: utf-8 -*-
"""
交易系統UI組件 - 修復完整版本
整合了完整的交易系統功能，支援多種初始化方式以保持向後兼容
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import uuid
import random

try:
    from .trade_recorder import TradeRecorder, TradeEntry
    from .trade_recorder import TradeType as TradeTypeEnum
    from .trade_recorder import TradeStatus as TradeStatusEnum
    from .trade_recorder import SignalType as SignalTypeEnum
    from .ai_advisor import create_ai_advisor
    from .signal_generator import create_signal_generator
    # 自動交易引擎可能不存在，使用try-except
    try:
        from ..automation.auto_trading_engine import create_auto_trading_engine
    except ImportError:
        create_auto_trading_engine = None
    
    # 嘗試導入自動數據抓取器
    try:
        from ..core.auto_data_fetcher import AutoDataFetcher
    except ImportError:
        AutoDataFetcher = None

    # 使用導入的枚舉
    TradeType = TradeTypeEnum
    TradeStatus = TradeStatusEnum
    SignalType = SignalTypeEnum
    
except ImportError:
    # 如果找不到模組，不提供 Mock 定義，直接報錯或設為 None
    TradeRecorder = None
    TradeEntry = None
    create_ai_advisor = None
    create_signal_generator = None
    create_auto_trading_engine = None

try:
    from jojo_trading.core.shioaji_connector import ShioajiConnector
except ImportError:
    ShioajiConnector = None

try:
    from jojo_trading.core.enhanced_dcf import IntegratedDCFHandler
except ImportError:
    IntegratedDCFHandler = None

try:
    from jojo_trading.core.yfinance_fetcher import YFinanceFetcher
except ImportError:
    YFinanceFetcher = None


class TradingSystemUI:
    """交易系統UI管理器 - 修復版本"""
    
    def __init__(self, trade_recorder=None):
        """
        初始化交易系統UI - 支援多種初始化方式
        
        Args:
            trade_recorder: 交易記錄器實例 (可選，向後兼容)
        """
        # 向後兼容的參數處理
        self.trade_recorder_param = trade_recorder
        
        # 初始化交易系統組件（使用session_state確保狀態持久化）
        if 'trade_recorder' not in st.session_state:
            if trade_recorder:
                st.session_state.trade_recorder = trade_recorder
            else:
                try:
                    if TradeRecorder:
                        st.session_state.trade_recorder = TradeRecorder()
                    else:
                        st.session_state.trade_recorder = None
                except:
                    st.session_state.trade_recorder = None

        if 'ai_advisor' not in st.session_state:
            try:
                if create_ai_advisor and st.session_state.trade_recorder:
                    st.session_state.ai_advisor = create_ai_advisor(st.session_state.trade_recorder)
                else:
                    st.session_state.ai_advisor = None
            except:
                st.session_state.ai_advisor = None

        if 'signal_generator' not in st.session_state:
            try:
                if create_signal_generator and st.session_state.trade_recorder and st.session_state.ai_advisor:
                    st.session_state.signal_generator = create_signal_generator(
                        st.session_state.trade_recorder, 
                        st.session_state.ai_advisor
                    )
                else:
                    st.session_state.signal_generator = None
            except:
                st.session_state.signal_generator = None

        if 'auto_trading_engine' not in st.session_state:
            try:
                if create_auto_trading_engine and st.session_state.trade_recorder and st.session_state.signal_generator:
                    st.session_state.auto_trading_engine = create_auto_trading_engine(
                        st.session_state.trade_recorder,
                        st.session_state.signal_generator
                    )
                else:
                    st.session_state.auto_trading_engine = None
            except:
                st.session_state.auto_trading_engine = None

        # 設置實例變數
        self.trade_recorder = st.session_state.trade_recorder
        self.ai_advisor = st.session_state.ai_advisor
        self.signal_generator = st.session_state.signal_generator
        self.auto_trading_engine = st.session_state.auto_trading_engine
        
        # 初始化自動數據抓取器
        if 'auto_fetcher' not in st.session_state:
            try:
                if AutoDataFetcher:
                    st.session_state.auto_fetcher = AutoDataFetcher()
                else:
                    st.session_state.auto_fetcher = None
            except:
                st.session_state.auto_fetcher = None
        self.auto_fetcher = st.session_state.auto_fetcher

        # Initialize Shioaji for Live Data
        if 'sj_connector' not in st.session_state:
            st.session_state.sj_connector = ShioajiConnector() if ShioajiConnector else None
        self.sj_connector = st.session_state.sj_connector

    @st.fragment(run_every=3)
    def render_live_ticker(self, symbol: str, label: str = None):
        """
        即時跳動報價組件 (每 3 秒刷新)
        支援股票 (e.g. "2330") 與 期貨 (e.g. "TXF", "MXF")
        """
        price, change_pct = self._fetch_price_universal(symbol)
        
        display_label = label if label else symbol
        
        if price > 0:
            color = "normal"
            if change_pct > 0:
                color = "normal" # Streamlit metric handles color by delta
            
            st.metric(
                label=display_label,
                value=f"{price:,.2f}",
                delta=f"{change_pct:.2f}%" if change_pct is not None else None
            )
        else:
            st.metric(label=display_label, value="---", delta=None)

    def _fetch_price_universal(self, symbol: str):
        """
        通用價格獲取 (股票 + 期貨)
        優先使用 Shioaji 即時源
        """
        price = 0.0
        change_pct = 0.0
        
        # 1. Try Shioaji (Real-Time)
        if self.sj_connector and self.sj_connector.is_connected:
            # Check if likely Future (Non-digit start or known codes)
            is_future = not symbol.isdigit() or symbol.startswith(('TX', 'MX', 'ZE'))
            
            if is_future:
                # Futures Snapshot
                snap = self.sj_connector.get_futures_snapshot(code=symbol[:3], specific_code=symbol if len(symbol)>3 else None)
                if snap:
                    price = snap.get('price', 0)
                    change_pct = snap.get('pct_change', 0)
                    return price, change_pct
            else:
                # Stock Snapshot
                p = self.sj_connector.get_latest_price(symbol)
                if p:
                    price = p
                    # Calculate change if open/ref available (Simplified here, just return price)
                    # Ideally get full snapshot for change
                    return price, 0.0 

        # 2. Fallback to AutoFetcher (Stocks only, cached/API)
        if self.auto_fetcher and symbol.isdigit():
             data = self.auto_fetcher.auto_fetch_stock_data(symbol)
             if data.get('success'):
                 price = data['data'].get('current_market_price', 0)
                 # derived change not always available in basic fetch
                 return price, 0.0
                 
        return price, change_pct

    def render(self):
        """渲染主要UI - 向後兼容方法"""
        self.render_trading_dashboard()
    
    def render_trading_dashboard(self):
        """渲染交易儀表板主頁面"""
        st.title("📊 智能交易系統儀表板")
        
        # 系統狀態檢查
        self._display_system_status()
        
        # 頁面選擇
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📈 總覽", "📝 交易記錄", "🤖 AI建議", "🔍 信號掃描", "⚙️ 設定"
        ])
        
        with tab1:
            self._render_overview_tab()
        
        with tab2:
            self._render_trade_records_tab()
        
        with tab3:
            self._render_ai_recommendations_tab()
        
        with tab4:
            self._render_signal_scanning_tab()
        
        with tab5:
            self._render_settings_tab()

    def _display_system_status(self):
        """顯示系統狀態"""
        # 檢查關鍵組件
        missing_components = []
        if not self.trade_recorder:
            missing_components.append("交易記錄器")
            
        if missing_components:
            st.error(f"⚠️ 關鍵功能未初始化: {', '.join(missing_components)}")
            st.warning("請先連接券商或檢查系統設定。在此狀態下目前僅提供有限的檢視功能，無法進行實際交易。")
            
    def _render_overview_tab(self):
        """渲染總覽頁面"""
        st.header("📊 投資組合總覽")
        
        # 檢查是否有交易記錄器
        if not self.trade_recorder:
            st.info("ℹ️ 請連接券商以查看投資組合。如需模擬交易，請前往「🎮 模擬專區」。")
            return

        
        # 完整模式的績效指標
        try:
            performance = self.trade_recorder.calculate_portfolio_performance()
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("總交易數", performance.get('total_trades', 0))
            
            with col2:
                total_pnl = performance.get('total_pnl', 0)
                st.metric("總損益", f"${total_pnl:.2f}", 
                         delta=f"{total_pnl:.2f}" if total_pnl != 0 else None)
            
            with col3:
                win_rate = performance.get('win_rate', 0)
                st.metric("勝率", f"{win_rate:.1f}%", 
                         delta=f"{win_rate-50:.1f}%" if win_rate != 0 else None)
            
            with col4:
                avg_return = performance.get('avg_return', 0)
                st.metric("平均回報", f"{avg_return:.2f}%", 
                         delta=f"{avg_return:.2f}%" if avg_return != 0 else None)
            
            # 開倉位置概況
            st.subheader("💼 當前持倉")
            open_trades = self.trade_recorder.get_open_trades()
            
            if open_trades:
                # 更新未實現損益
                for trade in open_trades:
                    current_price = self._get_current_price(trade.stock_code)
                    if hasattr(self.trade_recorder, 'update_unrealized_pnl'):
                        self.trade_recorder.update_unrealized_pnl(trade.stock_code, current_price)
                
                # 顯示持倉表格
                holdings_data = []
                for trade in open_trades:
                    current_price = self._get_current_price(trade.stock_code)
                    holdings_data.append({
                        '股票代碼': trade.stock_code,
                        '交易類型': trade.trade_type.value if hasattr(trade.trade_type, 'value') else str(trade.trade_type),
                        '進入價格': f"${trade.entry_price:.2f}",
                        '當前價格': f"${current_price:.2f}",
                        '數量': trade.quantity,
                        '未實現損益': f"${getattr(trade, 'unrealized_pnl', 0):.2f}",
                        '進入日期': trade.entry_time.strftime('%Y-%m-%d') if hasattr(trade, 'entry_time') else 'N/A',
                        '信號類型': trade.signal_type.value if hasattr(trade.signal_type, 'value') else str(trade.signal_type)
                    })
                
                df_holdings = pd.DataFrame(holdings_data)
                st.dataframe(df_holdings, use_container_width=True)
                
                # 持倉分析圖表
                self._render_holdings_chart(open_trades)
            else:
                st.info("🔍 目前沒有開倉位置")
            

            
            # 即時報價監視 (Watchlist Ticker)
            st.subheader("⚡ 即時報價 (Live Ticker)")
            cols = st.columns(4)
            watchlist = ["2330", "TXF", "2317", "MXF"] # Example mixed list
            for i, sym in enumerate(watchlist):
                with cols[i % 4]:
                    self.render_live_ticker(sym)

            # 最新市場洞察
            if self.ai_advisor:
                st.subheader("🎯 市場洞察")
                try:
                    market_insight = self.ai_advisor.generate_market_insight()
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**市場情緒:**", market_insight.get('market_sentiment', 'N/A'))
                        st.write("**最佳策略:**", market_insight.get('recommendations', {}).get('top_strategy', 'N/A'))
                    
                    with col2:
                        warnings = market_insight.get('recommendations', {}).get('risk_warning', [])
                        if warnings:
                            st.warning("⚠️ **風險警告:**")
                            for warning in warnings:
                                st.write(f"• {warning}")
                except Exception as e:
                    st.info("市場洞察功能暫時不可用")
                            
        except Exception as e:
            st.error(f"載入投資組合數據時發生錯誤: {str(e)}")

    def _render_trade_records_tab(self):
        """渲染交易記錄頁面"""
        st.header("📝 交易記錄管理")
        
        if not self.trade_recorder:
            st.info("ℹ️ 請連接券商以管理真實交易記錄。如需模擬交易，請前往「🎮 模擬專區」。")
            return

        
        # 手動新增交易記錄
        with st.expander("➕ 新增交易記錄"):
            self._render_add_trade_form()
        
        # 交易記錄篩選
        st.subheader("🔍 交易記錄篩選")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_filter = st.selectbox(
                "交易狀態",
                options=["全部", "開倉", "平倉", "部分平倉"],
                index=0
            )
        
        with col2:
            signal_options = ["全部", "DCF買入", "DCF賣出", "技術買入", "技術賣出", "手動"]
            try:
                if hasattr(SignalType, 'DCF_BUY'):
                    signal_options = ["全部"] + [signal.value for signal in SignalType]
            except:
                pass
            signal_filter = st.selectbox("信號類型", options=signal_options, index=0)
        
        with col3:
            date_range = st.date_input(
                "日期範圍",
                value=(datetime.now() - timedelta(days=30), datetime.now()),
                max_value=datetime.now()
            )
        
        # 顯示篩選後的交易記錄
        try:
            filtered_trades = self._filter_trades(status_filter, signal_filter, date_range)
            
            if filtered_trades:
                self._display_trade_records_table(filtered_trades)
                self._render_trade_statistics(filtered_trades)
                self._render_performance_charts(filtered_trades)
            else:
                st.info("🔍 沒有符合篩選條件的交易記錄")
        except Exception as e:
            st.error(f"載入交易記錄時發生錯誤: {str(e)}")


    def _render_ai_recommendations_tab(self):
        """渲染AI建議頁面"""
        st.header("🤖 AI投資建議")
        
        if not self.ai_advisor:
            st.info("ℹ️ AI 建議系統未連接。請確保已設定並連接券商系統。")
            return
        
        # 股票分析輸入
        col1, col2 = st.columns([2, 1])
        
        with col1:
            stock_code = st.text_input(
                "輸入股票代碼進行AI分析",
                placeholder="例如: 2330",
                key="ai_analysis_stock_input"
            )
        
        with col2:
            analyze_button = st.button("🔍 開始AI分析", type="primary")
        
        if analyze_button and stock_code:
            self._analyze_stock_with_ai(stock_code)
        
        # 顯示投資組合建議
        st.subheader("📋 投資組合建議")
        self._generate_portfolio_recommendations()




    def _render_signal_scanning_tab(self):
        """渲染信號掃描頁面"""
        st.header("🔍 市場信號掃描")
        
        # 監視列表
        st.subheader("👀 監視列表")
        
        # 默認監視列表
        default_watchlist = ["2330", "2317", "2454", "3008", "2412"]
        
        watchlist_input = st.text_area(
            "監視股票列表（一行一個股票代碼）",
            value="\n".join(default_watchlist),
            height=100
        )
        
        watchlist = [code.strip() for code in watchlist_input.split('\n') if code.strip()]
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔍 掃描進場信號", type="primary"):
                with st.spinner("掃描中..."):
                    self._scan_entry_signals(watchlist)
        
        with col2:
            if st.button("🚪 掃描出場信號"):
                with st.spinner("分析持倉..."):
                    self._scan_exit_signals()
        
        # 自動交易設定
        st.subheader("🤖 自動交易")
        
        if self.auto_trading_engine:
            auto_enabled = st.checkbox(
                "啟用自動交易",
                value=getattr(self.auto_trading_engine, 'auto_trade_enabled', False),
                help="啟用後系統將自動執行交易信號"
            )
            
            if hasattr(self.auto_trading_engine, 'enable_auto_trading'):
                if auto_enabled != getattr(self.auto_trading_engine, 'auto_trade_enabled', False):
                    self.auto_trading_engine.enable_auto_trading(auto_enabled)
                    st.success(f"自動交易已{'啟用' if auto_enabled else '停用'}")
            
            if auto_enabled:
                if st.button("▶️ 執行每日掃描"):
                    with st.spinner("執行自動交易掃描..."):
                        try:
                            if hasattr(self.auto_trading_engine, 'execute_daily_scan'):
                                result = self.auto_trading_engine.execute_daily_scan(watchlist)
                                st.json(result)
                            else:
                                st.info("自動掃描功能開發中...")
                        except Exception as e:
                            st.error(f"自動掃描失敗: {str(e)}")
        else:
            st.warning("⚠️ 自動交易引擎未初始化")
        
        # 顯示現有信號
        self._display_existing_signals()

    def _render_settings_tab(self):
        """渲染設定頁面"""
        st.header("⚙️ 系統設定")
        
        # 系統資訊
        st.subheader("📋 系統資訊")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**系統版本:** v2.0 (修復版)")
            st.write("**交易記錄器:** ✅ 已載入" if self.trade_recorder else "❌ 未載入")
            st.write("**AI建議:** ✅ 已載入" if self.ai_advisor else "❌ 未載入")
        
        with col2:
            st.write("**信號生成器:** ✅ 已載入" if self.signal_generator else "❌ 未載入")
            st.write("**自動交易:** ✅ 已載入" if self.auto_trading_engine else "❌ 未載入")
            st.write("**運行模式:** 完整模式" if self.trade_recorder else "簡化模式")
        
        # AI建議參數
        if self.signal_generator:
            st.subheader("🤖 AI建議參數")
            
            col1, col2 = st.columns(2)
            
            with col1:
                dcf_buy_threshold = st.slider(
                    "DCF買入折價門檻",
                    min_value=0.05,
                    max_value=0.30,
                    value=getattr(self.signal_generator, 'dcf_buy_threshold', 0.15),
                    step=0.01,
                    format="%.2f",
                    help="DCF估值低於市價的最小折價要求"
                )
                
                confidence_threshold = st.slider(
                    "最低信心度要求",
                    min_value=30,
                    max_value=90,
                    value=getattr(self.signal_generator, 'confidence_threshold', 60),
                    step=5,
                    help="交易信號的最低信心度要求"
                )
            
            with col2:
                dcf_sell_threshold = st.slider(
                    "DCF賣出溢價門檻",
                    min_value=-0.30,
                    max_value=-0.05,
                    value=getattr(self.signal_generator, 'dcf_sell_threshold', -0.10),
                    step=0.01,
                    format="%.2f",
                    help="DCF估值高於市價的最小溢價要求"
                )
                
                quality_threshold = st.slider(
                    "最低數據品質要求",
                    min_value=30,
                    max_value=80,
                    value=getattr(self.signal_generator, 'quality_min_threshold', 50),
                    step=5,
                    help="股票數據的最低品質要求"
                )
            
            # 更新參數
            if st.button("💾 儲存設定"):
                try:
                    if hasattr(self.signal_generator, 'dcf_buy_threshold'):
                        self.signal_generator.dcf_buy_threshold = dcf_buy_threshold
                        self.signal_generator.dcf_sell_threshold = dcf_sell_threshold
                        self.signal_generator.confidence_threshold = confidence_threshold
                        self.signal_generator.quality_min_threshold = quality_threshold
                    st.success("✅ 設定已儲存")
                except Exception as e:
                    st.error(f"儲存設定時發生錯誤: {str(e)}")
        
        # 資料管理
        st.subheader("📁 資料管理")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📥 匯出交易記錄"):
                try:
                    self._export_trade_records()
                except Exception as e:
                    st.error(f"匯出失敗: {str(e)}")
        
        with col2:
            if st.button("🔄 重新載入記錄"):
                try:
                    if self.trade_recorder and hasattr(self.trade_recorder, 'load_trades'):
                        self.trade_recorder.load_trades()
                        st.success("✅ 交易記錄已重新載入")
                    else:
                         st.warning("交易記錄器未連接")
                except Exception as e:
                    st.error(f"重新載入失敗: {str(e)}")
        
        with col3:
            if st.button("🗑️ 清除記錄", type="secondary"):
                st.warning("⚠️ 此功能需要確認，請聯繫管理員")

    # 輔助方法
    def _render_add_trade_form(self):
        """渲染新增交易表單"""
        if not self.trade_recorder:
            st.error("交易記錄器未初始化")
            return
            
        with st.form("add_trade_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                stock_code = st.text_input("股票代碼*", placeholder="例如: 2330")
                
                # 確保交易類型選項正確
                try:
                    if hasattr(TradeType, 'BUY'):
                        trade_type_options = [t.value for t in TradeType if hasattr(t, 'value')]
                    else:
                        trade_type_options = ["買入", "賣出"]
                except:
                    trade_type_options = ["買入", "賣出"]
                
                trade_type = st.selectbox("交易類型*", options=trade_type_options)
                entry_price = st.number_input("進入價格*", min_value=0.01, step=0.01)
                quantity = st.number_input("數量*", min_value=1, step=1)
            
            with col2:
                # 確保信號類型選項正確
                try:
                    if hasattr(SignalType, 'DCF_BUY'):
                        signal_type_options = [s.value for s in SignalType if hasattr(s, 'value')]
                    else:
                        signal_type_options = ["DCF買入", "DCF賣出", "技術買入", "技術賣出", "手動"]
                except:
                    signal_type_options = ["DCF買入", "DCF賣出", "技術買入", "技術賣出", "手動"]
                
                signal_type = st.selectbox("信號類型", options=signal_type_options)
                dcf_value = st.number_input("DCF內在價值", min_value=0.0, step=0.01)
                notes = st.text_area("備註", height=100)
            
            submitted = st.form_submit_button("➕ 新增交易記錄")
            
            if submitted:
                if stock_code and entry_price > 0 and quantity > 0:
                    try:
                        if TradeEntry and TradeType and SignalType:
                            trade = TradeEntry(
                                stock_code=stock_code,
                                stock_name=f"{stock_code}公司",
                                trade_type=TradeType.BUY if trade_type == "買入" else TradeType.SELL,
                                entry_price=entry_price,
                                quantity=quantity,
                                signal_type=self._convert_signal_type(signal_type),
                                dcf_intrinsic_value=dcf_value if dcf_value > 0 else None,
                                notes=notes
                            )
                            
                            trade_id = self.trade_recorder.add_trade(trade)
                            st.success(f"✅ 交易記錄已新增 (ID: {trade_id[:8]})")
                        else:
                             st.error("內部錯誤：交易類型或信號類型未定義")
                        
                        st.rerun()

                    except Exception as e:
                        st.error(f"新增失敗: {str(e)}")
                else:
                    st.error("❌ 請填寫所有必填欄位")

    def _convert_signal_type(self, signal_type_str):
        """轉換信號類型字符串到枚舉"""
        try:
            if SignalType and hasattr(SignalType, 'DCF_BUY'):
                signal_map = {
                    "DCF買入": SignalType.DCF_BUY,
                    "DCF賣出": SignalType.DCF_SELL,
                    "技術買入": SignalType.TECHNICAL_BUY,
                    "技術賣出": SignalType.TECHNICAL_SELL,
                    "手動": SignalType.MANUAL
                }
                return signal_map.get(signal_type_str, SignalType.MANUAL)
        except:
            pass
        return signal_type_str

    def _filter_trades(self, status_filter: str, signal_filter: str, date_range):
        """篩選交易記錄"""
        if not self.trade_recorder:
            return []
            
        try:
            trades = self.trade_recorder.trades.copy()
            
            # 狀態篩選
            if status_filter != "全部":
                if TradeStatus and hasattr(TradeStatus, 'OPEN'):
                    status_map = {
                        "開倉": TradeStatus.OPEN,
                        "平倉": TradeStatus.CLOSED,
                        "部分平倉": TradeStatus.PARTIAL
                    }
                    trades = [t for t in trades if t.status == status_map[status_filter]]
                else:
                    trades = [t for t in trades if str(t.status) == status_filter]
            
            # 信號類型篩選
            if signal_filter != "全部":
                trades = [t for t in trades if 
                         (hasattr(t.signal_type, 'value') and t.signal_type.value == signal_filter) or
                         str(t.signal_type) == signal_filter]
            
            # 日期篩選
            if len(date_range) == 2:
                start_date, end_date = date_range
                trades = [t for t in trades if 
                         hasattr(t, 'entry_time') and 
                         start_date <= t.entry_time.date() <= end_date]
            
            return trades
        except Exception as e:
            st.error(f"篩選交易記錄時發生錯誤: {str(e)}")
            return []

    def _filter_simple_trades(self, status_filter: str, signal_filter: str, date_range):
        """使用簡化模式篩選"""
        trades = self.trades.copy()
        
        # 狀態篩選
        if status_filter != "全部":
            trades = [t for t in trades if t.get('status') == status_filter]
        
        # 信號類型篩選
        if signal_filter != "全部":
            trades = [t for t in trades if t.get('signal_type') == signal_filter]
        
        return trades

    def _display_trade_records_table(self, trades):
        """顯示交易記錄表格"""
        trades_data = []
        
        for trade in trades:
            if hasattr(trade, 'trade_id'):  # 完整模式
                trades_data.append({
                    '交易ID': trade.trade_id[:8],
                    '股票代碼': trade.stock_code,
                    '股票名稱': trade.stock_name,
                    '類型': trade.trade_type.value if hasattr(trade.trade_type, 'value') else str(trade.trade_type),
                    '進入價格': f"${trade.entry_price:.2f}",
                    '出場價格': f"${trade.exit_price:.2f}" if hasattr(trade, 'exit_price') and trade.exit_price else "未平倉",
                    '數量': trade.quantity,
                    '實現損益': f"${trade.realized_pnl:.2f}" if hasattr(trade, 'realized_pnl') and trade.realized_pnl else "未實現",
                    '狀態': trade.status.value if hasattr(trade.status, 'value') else str(trade.status),
                    '信號': trade.signal_type.value if hasattr(trade.signal_type, 'value') else str(trade.signal_type),
                    '進入日期': trade.entry_time.strftime('%Y-%m-%d %H:%M') if hasattr(trade, 'entry_time') else 'N/A'
                })
            else:  # 簡化模式
                trades_data.append({
                    '交易ID': trade.get('trade_id', '')[:8],
                    '股票代碼': trade.get('stock_code', ''),
                    '股票名稱': trade.get('stock_name', ''),
                    '類型': trade.get('trade_type', ''),
                    '進入價格': f"${trade.get('entry_price', 0):.2f}",
                    '出場價格': f"${trade.get('exit_price', 0):.2f}" if trade.get('exit_price') else "未平倉",
                    '數量': trade.get('quantity', 0),
                    '實現損益': f"${trade.get('realized_pnl', 0):.2f}" if trade.get('realized_pnl') else "未實現",
                    '狀態': trade.get('status', ''),
                    '信號': trade.get('signal_type', ''),
                    '進入日期': trade.get('entry_time', 'N/A')
                })
        
        df_trades = pd.DataFrame(trades_data)
        st.dataframe(df_trades, use_container_width=True)

    def _get_current_price(self, stock_code: str) -> float:
        """獲取當前價格 (優先使用真實數據)"""
        # 嘗試使用 AutoDataFetcher 獲取真實價格
        if self.auto_fetcher:
            try:
                # 使用 auto_fetch_stock_data 獲取數據
                result = self.auto_fetcher.auto_fetch_stock_data(stock_code)
                if result['success'] and 'current_market_price' in result['data']:
                    price = result['data']['current_market_price']
                    if price and price > 0:
                        return float(price)
            except Exception as e:
                print(f"獲取真實價格失敗 {stock_code}: {e}")
        
        # 如果無法獲取真實數據，顯示警告並返回 0 (避免誤導)
        # 或者為了演示目的，如果真的獲取不到，可以保留一個標記
        return 0.0



    def _render_holdings_chart(self, open_trades):
        """渲染持倉分析圖表"""
        if not open_trades:
            return
            
        try:
            # 持倉分布餅圖
            holdings_value = []
            labels = []
            
            for trade in open_trades:
                current_price = self._get_current_price(trade.stock_code)
                value = current_price * trade.quantity
                holdings_value.append(value)
                labels.append(f"{trade.stock_code}")
            
            fig = px.pie(
                values=holdings_value,
                names=labels,
                title="持倉分布"
            )
            
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"渲染圖表時發生錯誤: {str(e)}")

    def _render_trade_statistics(self, trades):
        """渲染交易統計"""
        if not trades:
            return
            
        try:
            st.subheader("📊 交易統計")
            
            total_trades = len(trades)
            
            if self.trade_recorder and TradeStatus:
                # 使用完整模式統計
                closed_trades = [t for t in trades if 
                               (hasattr(t, 'status') and hasattr(t.status, 'value') and t.status == TradeStatus.CLOSED) or
                               str(t.status) == "平倉"]
                open_trades = [t for t in trades if 
                             (hasattr(t, 'status') and hasattr(t.status, 'value') and t.status == TradeStatus.OPEN) or
                             str(t.status) == "開倉"]
                winning_trades = [t for t in closed_trades if 
                                hasattr(t, 'realized_pnl') and t.realized_pnl and t.realized_pnl > 0]
            else:
                # 使用簡化模式統計
                closed_trades = [t for t in trades if t.get('status') == '平倉']
                open_trades = [t for t in trades if t.get('status') == '開倉']
                winning_trades = [t for t in closed_trades if t.get('realized_pnl', 0) > 0]
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("總交易數", total_trades)
            
            with col2:
                st.metric("開倉中", len(open_trades))
            
            with col3:
                win_rate = len(winning_trades) / len(closed_trades) * 100 if closed_trades else 0
                st.metric("勝率", f"{win_rate:.1f}%")
            
            with col4:
                if self.trade_recorder:
                    total_pnl = sum(getattr(t, 'realized_pnl', 0) or 0 for t in closed_trades)
                else:
                    total_pnl = sum(t.get('realized_pnl', 0) for t in closed_trades)
                st.metric("總損益", f"${total_pnl:.2f}")
                
        except Exception as e:
            st.error(f"計算統計時發生錯誤: {str(e)}")

    def _render_performance_charts(self, trades):
        """渲染績效圖表"""
        if not trades:
            return
            
        try:
            # 簡化的績效圖表
            st.subheader("📈 績效圖表")
            st.info("績效圖表功能開發中...")
        except Exception as e:
            st.error(f"渲染績效圖表時發生錯誤: {str(e)}")

    def _analyze_stock_with_ai(self, stock_code: str):
        """使用AI分析股票"""
        # 獲取真實數據
        real_data = {}
        current_price = 0.0
        
        if self.auto_fetcher:
            with st.spinner(f"正在抓取 {stock_code} 的真實數據..."):
                try:
                    fetch_result = self.auto_fetcher.get_dcf_ready_data(stock_code)
                    if fetch_result.get('success'):
                        real_data = fetch_result
                        current_price = real_data.get('current_market_price', 0.0)
                except Exception as e:
                    st.error(f"數據抓取失敗: {e}")

        if not self.ai_advisor:
            # 簡化的分析 (使用真實數據)
            if current_price == 0:
                current_price = self._get_current_price(stock_code)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader(f"📊 {stock_code} 基本面分析")
                if current_price > 0:
                    st.write(f"**當前價格:** ${current_price:.2f}")
                    
                    # 計算簡單指標
                    eps = real_data.get('net_income_parent', 0) / real_data.get('shares_outstanding', 1) if real_data else 0
                    pe = current_price / eps if eps > 0 else 0
                    
                    if pe > 0:
                        st.write(f"**本益比 (Est):** {pe:.1f}")
                    
                    if real_data:
                        st.write(f"**年度淨利:** {real_data.get('net_income_parent', 0)/1e8:.1f}億")
                        st.write(f"**資料來源:** {real_data.get('data_sources', {}).get('current_market_price', '未知')}")
                else:
                    st.warning("無法獲取即時股價")
            
            with col2:
                st.subheader("💡 分析建議")
                if real_data:
                    quality_score = real_data.get('data_quality_score', 0)
                    st.write(f"**數據品質:** {quality_score:.0f}%")
                    
                    if quality_score > 60:
                        st.success("數據完整，可進行深入分析")
                    else:
                        st.warning("數據不足，建議謹慎參考")
                else:
                    st.info("請檢查網絡連接或數據源")
            return
            
        try:
            # 完整AI分析
            if current_price == 0:
                current_price = self._get_current_price(stock_code)
            
            # 構建分析數據 (優先使用真實數據)
            analysis_data = {
                'current_price': current_price,
                'pe_ratio': 0, # 需計算
                'pb_ratio': 0, # 需計算
                'roe': 0,      # 需計算
                'debt_ratio': 0,
                'revenue_growth': 0,
                'validation_score': real_data.get('data_quality_score', 50) if real_data else 50
            }
            
            # 如果有真實數據，補充指標
            if real_data:
                net_income = real_data.get('net_income_parent', 0)
                shares = real_data.get('shares_outstanding', 1)
                eps = net_income / shares if shares > 0 else 0
                if eps > 0 and current_price > 0:
                    analysis_data['pe_ratio'] = current_price / eps
                
                # 這裡可以加入更多真實指標計算...
                
                # 3. [NEW] 計算 DCF 內在價值
                try:
                    dcf_handler = IntegratedDCFHandler()
                    
                    # 準備 DCF 輸入數據 (優先使用 FCF，若無則嘗試用淨利近似)
                    dcf_input = []
                    if real_data.get('fcf'):
                        # 假設 FCF 為此單一年度值，簡單預測未來 5 年 (固定成長)
                        base_fcf = real_data['fcf']
                        dcf_input = [base_fcf * (1.05 ** i) for i in range(5)]
                    elif real_data.get('net_income_parent'):
                        # 簡易代理: Net Income + Dep - Capex (若無 Capex 則設為 0)
                        ni = real_data.get('net_income_parent')
                        dep = real_data.get('depreciation', 0) or 0
                        capex = real_data.get('capex', 0) or 0 # 注意: Capex 通常為負值? 需確認 DataAdapter
                        # DataAdapter 中 standardized["capex"] = yf_data.get("capex") -> Yahoo Capex 是負數
                        # 所以 FCF = NI + Dep + Capex (加上負數)
                        # 但為保安全，我們檢查 Capex 符號
                        if capex > 0: capex = -capex # 強制轉負
                        
                        fcf_proxy = ni + dep + capex
                        dcf_input = [fcf_proxy * (1.05 ** i) for i in range(5)]
                    
                    if dcf_input:
                        total_enterprise_value = dcf_handler.calculate_dcf_value(dcf_input)
                        
                        # 加上現金，減去債務 => 股權價值
                        cash = real_data.get('cash', 0) or 0
                        debt = real_data.get('total_debt', 0) or 0
                        equity_value = total_enterprise_value + cash - debt
                        
                        shares = real_data.get('shares_outstanding', 1) or 1
                        intrinsic_value_per_share = equity_value / shares
                        
                        # 更新到分析數據 (關鍵修正: AIAdvisor 讀取的是 intrinsic_value_per_share)
                        if intrinsic_value_per_share > 0:
                            analysis_data['intrinsic_value_per_share'] = intrinsic_value_per_share
                            # 向下兼容
                            analysis_data['dcf_intrinsic_value'] = intrinsic_value_per_share
                
                except Exception as e:
                    st.error(f"DCF 計算錯誤: {str(e)}")
                    # 顯示調試信息
                    # st.write(f"Debug Info: NI={real_data.get('net_income_parent')}, Dep={real_data.get('depreciation')}")

            # [Phase 4] 獲取歷史價格數據
            price_history = None
            if YFinanceFetcher:
                price_history = YFinanceFetcher.get_price_history(stock_code)

            # AI分析 (傳入價格歷史)
            analysis = self.ai_advisor.analyze_stock(stock_code, analysis_data, current_price, price_history)
            signal = self.ai_advisor.generate_trading_signal(analysis)
            
            # 顯示分析結果
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader(f"📊 {stock_code} 基本面分析")
                st.write(f"**當前價格:** ${current_price:.2f}")
                
                # F-Score Display
                f_score = getattr(analysis, 'piotroski_f_score', 0)
                f_color = "green" if f_score >= 7 else "orange" if f_score >= 4 else "red"
                st.markdown(f"**F-Score:** :{f_color}[{f_score}/9] (財務體質)")
                
                dcf_val = getattr(analysis, 'dcf_intrinsic_value', None)
                st.write(f"**DCF內在價值:** ${dcf_val if dcf_val is not None else 0:.2f}")
                
                if analysis_data['pe_ratio'] > 0:
                    st.write(f"**本益比:** {analysis_data['pe_ratio']:.1f}")
                
                if real_data:
                     st.caption(f"數據來源: {real_data.get('data_sources', 'AutoFetcher')}")
            
            with col2:
                st.subheader("🎯 AI評分")
                score = getattr(analysis, 'overall_score', 0)
                st.progress(score / 100, text=f"綜合評分: {score:.0f}/100")
                
                # Technical Display
                if analysis.rsi is not None:
                    st.write(f"**RSI:** {analysis.rsi:.1f}")
                
                if analysis.ma_trend:
                    trend_icon = "📈" if analysis.ma_trend == "Bullish" else "📉" if analysis.ma_trend == "Bearish" else "➡️"
                    st.write(f"**趨勢:** {trend_icon} {analysis.ma_trend}")
            
            # 顯示交易信號
            if signal:
                action = getattr(signal, 'action', 'HOLD')
                if hasattr(action, 'value'):
                    action = action.value
                
                if action == 'BUY':
                    st.success(f"🎯 **AI建議:** {action}")
                elif action == 'SELL':
                    st.error(f"🎯 **AI建議:** {action}")
                else:
                    st.info(f"🎯 **AI建議:** {action}")
                    
                st.write(f"**信心度:** {getattr(signal, 'confidence', 0):.0f}%")
                tgt_price = getattr(signal, 'target_price', None)
                st.write(f"**目標價格:** ${tgt_price if tgt_price is not None else 0:.2f}")
                st.write(f"**建議理由:** {getattr(signal, 'reasoning', '基於基本面分析')}")
                
                # [Phase 5] Auto Trader Integration
                if action in ['BUY', 'SELL'] and self.broker_connected:
                    st.markdown("---")
                    if st.button(f"⚡ 立即執行 ({action})", key=f"quick_exec_{stock_code}", type="primary"):
                        st.session_state[f"show_order_{stock_code}"] = True
                    
                    if st.session_state.get(f"show_order_{stock_code}", False):
                        with st.container(border=True):
                            st.markdown(f"**確認下單: {stock_code}**")
                            q_price = st.number_input("價格", value=current_price, key=f"q_p_{stock_code}")
                            q_qty = st.number_input("數量 (張)", value=1, min_value=1, key=f"q_q_{stock_code}")
                            
                            if st.button("🚀 確認送出", key=f"q_sub_{stock_code}", type="primary"):
                                # 呼叫下單邏輯 (需確保 ShioajiConnector 可用)
                                try:
                                    if self.sj_connector:
                                        # 使用市價或限價
                                        order_res = self.sj_connector.place_order(
                                            stock_code=stock_code,
                                            action=action, # Buy/Sell
                                            price=q_price,
                                            quantity=q_qty,
                                            price_type="LMT", # 限價
                                            order_type="ROD"  # 當日有效
                                        )
                                        st.success(f"下單成功! 單號: {order_res.get('order_id', 'Unknown')}")
                                        st.session_state[f"show_order_{stock_code}"] = False # 關閉面板
                                    else:
                                        st.error("券商未連線")
                                except Exception as e_ord:
                                    st.error(f"下單失敗: {e_ord}")
                
        except Exception as e:
            st.error(f"AI分析時發生錯誤: {str(e)}")

    def _generate_portfolio_recommendations(self):
        """生成投資組合建議"""
        try:
            recommendations = [
                "基於當前市場條件，建議增加科技股配置",
                "考慮分散投資到不同產業以降低風險",
                "注意美股市場動向對台股的影響",
                "建議定期檢視投資組合平衡"
            ]
            
            for i, rec in enumerate(recommendations, 1):
                st.write(f"{i}. {rec}")
                
        except Exception as e:
            st.error(f"生成建議時發生錯誤: {str(e)}")

    def _scan_entry_signals(self, watchlist: List[str]):
        """掃描進場信號 (使用真實數據)"""
        try:
            if not watchlist:
                st.warning("請先設定監視列表")
                return
            
            results = []
            progress_bar = st.progress(0)
            
            for i, stock in enumerate(watchlist):
                progress_bar.progress((i + 1) / len(watchlist))
                
                # 獲取真實數據
                real_data = None
                current_price = 0
                intrinsic_value = 0
                
                if self.auto_fetcher:
                    try:
                        fetch_result = self.auto_fetcher.get_dcf_ready_data(stock)
                        if fetch_result.get('success'):
                            real_data = fetch_result
                            current_price = real_data.get('current_market_price', 0)
                            
                            # 簡單估值邏輯 (如果沒有 AI Advisor)
                            # 這裡可以調用 IntegratedDCFHandler 如果有的話，但為了簡單起見，我們先用簡單邏輯
                            # 或者如果 fetch_result 裡已經有 intrinsic_value (目前沒有，需要計算)
                            
                            # 嘗試計算內在價值 (使用簡單 DCF)
                            net_income = real_data.get('net_income_parent', 0)
                            shares = real_data.get('shares_outstanding', 1)
                            eps = net_income / shares if shares > 0 else 0
                            if eps > 0:
                                # 假設 8% 成長, 10% 折現, 5年
                                intrinsic_value = eps * 15 # 簡單 PE 估值作為替代
                            
                    except Exception:
                        pass
                
                if current_price == 0:
                    current_price = self._get_current_price(stock)

                # 生成信號
                signal = 'HOLD'
                confidence = 50
                reason = '數據不足'
                
                if current_price > 0 and intrinsic_value > 0:
                    upside = (intrinsic_value / current_price) - 1
                    if upside > 0.2:
                        signal = 'BUY'
                        confidence = min(60 + int(upside * 100), 90)
                        reason = f'估值低估 {upside:.1%}'
                    elif upside < -0.2:
                        signal = 'SELL'
                        confidence = min(60 + int(abs(upside) * 100), 90)
                        reason = f'估值高估 {abs(upside):.1%}'
                    else:
                        reason = '估值合理'
                
                if signal != 'HOLD':
                    results.append({
                        'stock_code': stock,
                        'signal': signal,
                        'confidence': confidence,
                        'reason': reason,
                        'price': current_price,
                        'value': intrinsic_value
                    })
            
            progress_bar.empty()
            
            if results:
                st.success(f"🎯 發現 {len(results)} 個交易信號")
                for result in results:
                    color = "🟢" if result['signal'] == 'BUY' else "🔴"
                    with st.expander(f"{color} {result['stock_code']} - {result['signal']} (信心度: {result['confidence']}%)"):
                        st.write(f"**當前價格:** ${result['price']:.2f}")
                        st.write(f"**估算價值:** ${result['value']:.2f}")
                        st.write(f"**理由:** {result['reason']}")
            else:
                st.info("🔍 目前沒有發現明顯的交易信號")
                
        except Exception as e:
            st.error(f"掃描信號時發生錯誤: {str(e)}")

    def _scan_exit_signals(self):
        """掃描出場信號 (使用真實數據)"""
        try:
            if self.trade_recorder and hasattr(self.trade_recorder, 'get_open_trades'):
                open_trades = self.trade_recorder.get_open_trades()
            else:
                # 簡化模式下的持倉
                open_trades = [t for t in self.trades if isinstance(t, dict) and t.get('status') == '開倉']
            
            if not open_trades:
                st.info("目前沒有持倉需要分析")
                return

            results = []
            progress_bar = st.progress(0)
            
            for i, trade in enumerate(open_trades):
                progress_bar.progress((i + 1) / len(open_trades))
                
                stock_code = trade.stock_code if hasattr(trade, 'stock_code') else trade.get('stock_code')
                entry_price = trade.entry_price if hasattr(trade, 'entry_price') else trade.get('entry_price', 0)
                
                # 獲取真實數據
                current_price = 0
                intrinsic_value = 0
                
                if self.auto_fetcher:
                    try:
                        fetch_result = self.auto_fetcher.get_dcf_ready_data(stock_code)
                        if fetch_result.get('success'):
                            real_data = fetch_result
                            current_price = real_data.get('current_market_price', 0)
                            
                            # 簡單估值邏輯
                            net_income = real_data.get('net_income_parent', 0)
                            shares = real_data.get('shares_outstanding', 1)
                            eps = net_income / shares if shares > 0 else 0
                            if eps > 0:
                                intrinsic_value = eps * 15 
                    except Exception:
                        pass
                
                if current_price == 0:
                    current_price = self._get_current_price(stock_code)
                
                # 生成出場信號
                signal = 'HOLD'
                reason = '持有中'
                
                if current_price > 0:
                    # 獲利出場條件
                    if entry_price > 0:
                        pnl_pct = (current_price - entry_price) / entry_price
                        if pnl_pct > 0.2: # 獲利 20%
                            signal = 'SELL'
                            reason = f'獲利達標 ({pnl_pct:.1%})'
                        elif pnl_pct < -0.15: # 停損 15%
                            signal = 'SELL'
                            reason = f'觸發停損 ({pnl_pct:.1%})'
                    
                    # 估值出場條件
                    if intrinsic_value > 0:
                        upside = (intrinsic_value / current_price) - 1
                        if upside < -0.1: # 價格高於價值 10%
                            signal = 'SELL'
                            reason = f'估值過高 (溢價 {abs(upside):.1%})'
                
                if signal == 'SELL':
                    results.append({
                        'stock_code': stock_code,
                        'signal': signal,
                        'reason': reason,
                        'price': current_price,
                        'entry': entry_price
                    })

            progress_bar.empty()
            
            if results:
                st.warning(f"⚠️ 發現 {len(results)} 個出場信號")
                for result in results:
                    with st.expander(f"🔴 {result['stock_code']} - 建議賣出"):
                        st.write(f"**當前價格:** ${result['price']:.2f}")
                        st.write(f"**買入價格:** ${result['entry']:.2f}")
                        st.write(f"**理由:** {result['reason']}")
            else:
                st.success("✅ 目前持倉穩健，未發現明顯出場信號")
                
        except Exception as e:
            st.error(f"掃描出場信號時發生錯誤: {str(e)}")

    def _display_existing_signals(self):
        """顯示現有信號"""
        st.subheader("📡 最新交易信號")
        
        # 這裡可以連接到 SignalGenerator 獲取歷史信號
        # 目前僅顯示提示
        st.info("請點擊上方按鈕進行信號掃描")
        
        # 如果有自動交易引擎，可以顯示其日誌中的信號
        if self.auto_trading_engine and hasattr(self.auto_trading_engine, 'get_recent_signals'):
            try:
                signals = self.auto_trading_engine.get_recent_signals()
                if signals:
                    for signal in signals:
                        st.write(signal)
            except:
                pass

    def _export_trade_records(self):
        """匯出交易記錄"""
        try:
            # 簡化的匯出功能
            st.success("✅ 交易記錄匯出功能開發中")
            st.info("即將支援CSV和Excel格式匯出")
        except Exception as e:
            st.error(f"匯出時發生錯誤: {str(e)}")

# 確保類可以被正確導入
__all__ = ['TradingSystemUI']
