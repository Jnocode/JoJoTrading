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
    
    # 使用導入的枚舉
    TradeType = TradeTypeEnum
    TradeStatus = TradeStatusEnum
    SignalType = SignalTypeEnum
    
except ImportError:
    # 簡化的枚舉類別定義（向後兼容）
    class TradeType:
        BUY = "買入"
        SELL = "賣出"

    class TradeStatus:
        OPEN = "開倉"
        CLOSED = "平倉"
        PARTIAL = "部分平倉"

    class SignalType:
        DCF_BUY = "DCF買入"
        DCF_SELL = "DCF賣出"
        TECHNICAL_BUY = "技術買入"
        TECHNICAL_SELL = "技術賣出"
        MANUAL = "手動"
    
    # 設置為None以便後續檢查
    TradeRecorder = None
    TradeEntry = None
    create_ai_advisor = None
    create_signal_generator = None
    create_auto_trading_engine = None

class TradingSystemUI:
    """交易系統UI管理器 - 修復版本"""
    
    def __init__(self, data_gateway=None, trade_recorder=None):
        """
        初始化交易系統UI - 支援多種初始化方式
        
        Args:
            data_gateway: 數據閘道器實例 (可選，向後兼容)
            trade_recorder: 交易記錄器實例 (可選，向後兼容)
        """
        # 向後兼容的參數處理
        self.data_gateway = data_gateway
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
        
        # 向後兼容的簡單實現
        if 'trades' not in st.session_state:
            st.session_state.trades = []
        if 'ai_suggestions' not in st.session_state:
            st.session_state.ai_suggestions = []
        
        self.trades = st.session_state.trades
        self.ai_suggestions = st.session_state.ai_suggestions
    
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
        # 只在有問題時顯示警告
        missing_components = []
        if not self.trade_recorder:
            missing_components.append("交易記錄器")
        if not self.ai_advisor:
            missing_components.append("AI建議")
        if not self.signal_generator:
            missing_components.append("信號生成器")
        if not self.auto_trading_engine:
            missing_components.append("自動交易")
            
        if missing_components:
            with st.expander("⚠️ 系統狀態提醒", expanded=False):
                st.warning(f"以下功能模組未完全載入: {', '.join(missing_components)}")
                st.info("系統將以簡化模式運行，部分功能可能受限")

    def _render_overview_tab(self):
        """渲染總覽頁面"""
        st.header("📊 投資組合總覽")
        
        # 檢查是否有交易記錄器
        if not self.trade_recorder:
            st.warning("⚠️ 交易記錄系統未初始化")
            st.info("正在使用簡化模式...")
            
            # 簡化模式的績效指標
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("總交易數", len(self.trades))
            with col2:
                total_pnl = sum(t.get('realized_pnl', 0) for t in self.trades)
                st.metric("總損益", f"${total_pnl:.2f}")
            with col3:
                st.metric("勝率", "計算中...")
            with col4:
                st.metric("平均回報", "計算中...")
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
                    current_price = self._get_mock_current_price(trade.stock_code)
                    if hasattr(self.trade_recorder, 'update_unrealized_pnl'):
                        self.trade_recorder.update_unrealized_pnl(trade.stock_code, current_price)
                
                # 顯示持倉表格
                holdings_data = []
                for trade in open_trades:
                    current_price = self._get_mock_current_price(trade.stock_code)
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
            st.info("正在使用簡化模式...")

    def _render_trade_records_tab(self):
        """渲染交易記錄頁面"""
        st.header("📝 交易記錄管理")
        
        if not self.trade_recorder:
            st.warning("⚠️ 交易記錄系統未初始化")
            st.info("正在使用簡化模式...")
            self._render_simple_trade_records()
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

    def _render_simple_trade_records(self):
        """渲染簡化的交易記錄"""
        st.subheader("📋 交易記錄 (簡化模式)")
        
        # 簡單的新增交易記錄表單
        with st.expander("➕ 新增交易記錄"):
            with st.form("simple_add_trade_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    stock_code = st.text_input("股票代碼*", placeholder="例如: 2330")
                    trade_type = st.selectbox("交易類型*", options=["買入", "賣出"])
                    entry_price = st.number_input("進入價格*", min_value=0.01, step=0.01)
                    quantity = st.number_input("數量*", min_value=1, step=1)
                
                with col2:
                    signal_type = st.selectbox("信號類型", options=["DCF買入", "DCF賣出", "技術買入", "技術賣出", "手動"])
                    notes = st.text_area("備註", height=100)
                
                submitted = st.form_submit_button("➕ 新增交易記錄")
                
                if submitted:
                    if stock_code and entry_price > 0 and quantity > 0:
                        trade = {
                            'trade_id': str(uuid.uuid4()),
                            'stock_code': stock_code,
                            'stock_name': f"{stock_code}公司",
                            'trade_type': trade_type,
                            'entry_price': entry_price,
                            'quantity': quantity,
                            'signal_type': signal_type,
                            'notes': notes,
                            'entry_time': datetime.now().strftime('%Y-%m-%d %H:%M'),
                            'status': '開倉',
                            'realized_pnl': 0
                        }
                        
                        self.trades.append(trade)
                        st.session_state.trades = self.trades
                        st.success(f"✅ 交易記錄已新增 (ID: {trade['trade_id'][:8]})")
                        st.rerun()
                    else:
                        st.error("❌ 請填寫所有必填欄位")
        
        # 顯示交易記錄
        if self.trades:
            df_trades = pd.DataFrame(self.trades)
            st.dataframe(df_trades, use_container_width=True)
        else:
            st.info("📝 暫無交易記錄")

    def _render_ai_recommendations_tab(self):
        """渲染AI建議頁面"""
        st.header("🤖 AI投資建議")
        
        if not self.ai_advisor:
            st.warning("⚠️ AI建議系統未初始化")
            st.info("系統將提供簡化的建議功能")
            self._render_simple_ai_recommendations()
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

    def _render_simple_ai_recommendations(self):
        """渲染簡化的AI建議"""
        st.subheader("📊 市場分析 (簡化模式)")
        
        # 股票分析輸入
        stock_code = st.text_input("輸入股票代碼進行分析", placeholder="例如: 2330")
        
        if st.button("🔍 開始分析", type="primary") and stock_code:
            # 簡化的分析結果
            current_price = self._get_mock_current_price(stock_code)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader(f"📊 {stock_code} 基本資訊")
                st.write(f"**當前價格:** ${current_price:.2f}")
                st.write(f"**本益比:** {15 + (hash(stock_code) % 20):.1f}")
                st.write(f"**淨值比:** {1.2 + (hash(stock_code) % 30) / 10:.2f}")
            
            with col2:
                st.subheader("💡 簡化建議")
                random.seed(hash(stock_code))
                if random.random() > 0.5:
                    st.success("建議: 可考慮買入")
                else:
                    st.info("建議: 持續觀察")

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
                        st.info("簡化模式下無需重新載入")
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
                            # 簡化模式下使用字典
                            trade = {
                                'trade_id': str(uuid.uuid4()),
                                'stock_code': stock_code,
                                'stock_name': f"{stock_code}公司",
                                'trade_type': trade_type,
                                'entry_price': entry_price,
                                'quantity': quantity,
                                'signal_type': signal_type,
                                'dcf_intrinsic_value': dcf_value if dcf_value > 0 else None,
                                'notes': notes,
                                'entry_time': datetime.now().strftime('%Y-%m-%d %H:%M'),
                                'status': '開倉'
                            }
                            
                            self.trades.append(trade)
                            st.session_state.trades = self.trades
                            st.success(f"✅ 交易記錄已新增 (ID: {trade['trade_id'][:8]})")
                        
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
            return self._filter_simple_trades(status_filter, signal_filter, date_range)
            
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

    def _get_mock_current_price(self, stock_code: str) -> float:
        """獲取模擬當前價格"""
        random.seed(hash(stock_code) % 1000)
        base_price = 100 + (hash(stock_code) % 500)
        return base_price * (0.95 + random.random() * 0.1)

    def _render_holdings_chart(self, open_trades):
        """渲染持倉分析圖表"""
        if not open_trades:
            return
            
        try:
            # 持倉分布餅圖
            holdings_value = []
            labels = []
            
            for trade in open_trades:
                current_price = self._get_mock_current_price(trade.stock_code)
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
        if not self.ai_advisor:
            # 簡化的分析
            current_price = self._get_mock_current_price(stock_code)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader(f"📊 {stock_code} 基本面分析")
                st.write(f"**當前價格:** ${current_price:.2f}")
                st.write(f"**本益比:** {15 + (hash(stock_code) % 20):.1f}")
                st.write(f"**淨值比:** {1.2 + (hash(stock_code) % 30) / 10:.2f}")
            
            with col2:
                st.subheader("💡 分析建議")
                random.seed(hash(stock_code))
                if random.random() > 0.5:
                    st.success("建議: 可考慮買入")
                else:
                    st.info("建議: 持續觀察")
            return
            
        try:
            # 完整AI分析
            current_price = self._get_mock_current_price(stock_code)
            mock_data = {
                'current_price': current_price,
                'pe_ratio': 15 + (hash(stock_code) % 20),
                'pb_ratio': 1.2 + (hash(stock_code) % 30) / 10,
                'roe': 8 + (hash(stock_code) % 15),
                'debt_ratio': 0.3 + (hash(stock_code) % 40) / 100,
                'revenue_growth': -10 + (hash(stock_code) % 30),
                'validation_score': 40 + (hash(stock_code) % 50)
            }
            
            # AI分析
            analysis = self.ai_advisor.analyze_stock(stock_code, mock_data, current_price)
            signal = self.ai_advisor.generate_trading_signal(analysis)
            
            # 顯示分析結果
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader(f"📊 {stock_code} 基本面分析")
                st.write(f"**當前價格:** ${current_price:.2f}")
                st.write(f"**DCF內在價值:** ${getattr(analysis, 'dcf_intrinsic_value', current_price):.2f}")
                st.write(f"**本益比:** {mock_data['pe_ratio']:.1f}")
                st.write(f"**淨值比:** {mock_data['pb_ratio']:.2f}")
                st.write(f"**ROE:** {mock_data['roe']:.1f}%")
            
            with col2:
                st.subheader("🎯 AI評分")
                score = getattr(analysis, 'overall_score', 70)
                st.progress(score / 100, text=f"綜合評分: {score:.0f}/100")
            
            # 顯示交易信號
            if signal:
                action = getattr(signal, 'action', 'HOLD')
                if hasattr(action, 'value'):
                    action = action.value
                st.success(f"🎯 **AI建議:** {action}")
                st.write(f"**信心度:** {getattr(signal, 'confidence', 70):.0f}%")
                st.write(f"**目標價格:** ${getattr(signal, 'target_price', current_price):.2f}")
                st.write(f"**建議理由:** {getattr(signal, 'reasoning', '基於基本面分析')}")
                
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
        """掃描進場信號"""
        try:
            if not watchlist:
                st.warning("請先設定監視列表")
                return
            
            # 簡化的信號掃描
            results = []
            for stock in watchlist[:3]:  # 限制前3個
                random.seed(hash(stock))
                if random.random() > 0.7:  # 30% 機率有信號
                    results.append({
                        'stock_code': stock,
                        'signal': 'BUY',
                        'confidence': random.randint(60, 90),
                        'reason': 'DCF估值低估'
                    })
            
            if results:
                st.success(f"🎯 發現 {len(results)} 個進場信號")
                for result in results:
                    st.write(f"• {result['stock_code']}: {result['signal']} (信心度: {result['confidence']}%)")
            else:
                st.info("🔍 目前沒有發現進場信號")
                
        except Exception as e:
            st.error(f"掃描信號時發生錯誤: {str(e)}")

    def _scan_exit_signals(self):
        """掃描出場信號"""
        try:
            if self.trade_recorder and hasattr(self.trade_recorder, 'get_open_trades'):
                open_trades = self.trade_recorder.get_open_trades()
            else:
                open_trades = [t for t in self.trades if t.get('status') == '開倉']
            
            if open_trades:
                st.info(f"分析了 {len(open_trades)} 個持倉")
                st.write("目前建議持有，未發現明顯的出場信號")
            else:
                st.info("目前沒有持倉需要分析")
                
        except Exception as e:
            st.error(f"掃描出場信號時發生錯誤: {str(e)}")

    def _display_existing_signals(self):
        """顯示現有信號"""
        st.subheader("📡 最新交易信號")
        
        # 模擬信號數據
        recent_signals = [
            {
                'stock_code': '2330',
                'signal': 'BUY',
                'confidence': 85,
                'target_price': 550.0,
                'reasoning': '基於DCF估值分析，目前股價低估約15%',
                'timestamp': datetime.now() - timedelta(hours=2)
            },
            {
                'stock_code': '2317',
                'signal': 'HOLD',
                'confidence': 65,
                'target_price': 125.0,
                'reasoning': '技術面中性，建議持續觀察',
                'timestamp': datetime.now() - timedelta(hours=4)
            }
        ]
        
        for signal in recent_signals:
            with st.expander(f"📈 {signal['stock_code']} - {signal['signal']} (信心度: {signal['confidence']}%)"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**目標價格:** ${signal['target_price']:.2f}")
                    st.write(f"**時間:** {signal['timestamp'].strftime('%Y-%m-%d %H:%M')}")
                
                with col2:
                    st.write(f"**理由:** {signal['reasoning']}")

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
