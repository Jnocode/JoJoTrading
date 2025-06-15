# -*- coding: utf-8 -*-
"""
交易系統UI組件 - 統一版本
用於在Streamlit應用中展示交易記錄、AI建議和績效報告
支援多種運行模式：完整模式和簡化模式
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
import uuid
import logging
import random

# 初始化日誌
logger = logging.getLogger(__name__)

# 簡化的枚舉類別定義（備用）
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

class TradingSystemUI:
    """交易系統UI管理器 - 統一版本"""
    
    def __init__(self, trade_recorder=None, signal_analyzer=None, auto_trading_engine=None):
        """
        初始化交易系統UI
        
        Args:
            trade_recorder: 交易記錄器（可選）
            signal_analyzer: 信號分析器（可選）
            auto_trading_engine: 自動交易引擎（可選）
        """
        logger.info("初始化交易系統UI - 統一版本")
        
        # 嘗試初始化交易記錄器
        self.trade_recorder = trade_recorder
        if trade_recorder is None:
            try:
                from .trade_recorder import TradeRecorder
                self.trade_recorder = TradeRecorder()
                logger.info("TradeRecorder初始化成功")
            except (ImportError, Exception) as e:
                logger.warning(f"TradeRecorder初始化失敗: {e}")
                self.trade_recorder = None
        
        # 嘗試初始化信號分析器
        self.signal_analyzer = signal_analyzer
        if signal_analyzer is None:
            try:
                from ..analysis.signal_analyzer import SignalAnalyzer
                self.signal_analyzer = SignalAnalyzer()
                logger.info("SignalAnalyzer初始化成功")
            except (ImportError, Exception) as e:
                logger.warning(f"SignalAnalyzer初始化失敗: {e}")
                self.signal_analyzer = None
        
        # 嘗試初始化自動交易引擎
        self.auto_trading_engine = auto_trading_engine
        if auto_trading_engine is None:
            try:
                from ..automation.auto_trading_engine import create_auto_trading_engine
                self.auto_trading_engine = create_auto_trading_engine()
                logger.info("AutoTradingEngine初始化成功")
            except (ImportError, Exception) as e:
                logger.warning(f"AutoTradingEngine初始化失敗: {e}")
                self.auto_trading_engine = None
          # 初始化運行模式
        self.full_mode = all([self.trade_recorder, self.signal_analyzer, self.auto_trading_engine])
        logger.info(f"運行模式: {'完整模式' if self.full_mode else '簡化模式'}")
        
        # 初始化簡化模式的數據（如果需要）
        self._initialize_simple_mode_data()
    
    def _initialize_simple_mode_data(self):
        """初始化簡化模式下的數據"""
        if 'trades' not in st.session_state:
            st.session_state.trades = []
        
        if 'ai_suggestions' not in st.session_state:
            st.session_state.ai_suggestions = []
        
        if 'signal_scan_results' not in st.session_state:
            st.session_state.signal_scan_results = []
    
    def _safe_get_attr(self, obj, attr_name, default=None):
        """安全獲取對象屬性"""
        try:
            return getattr(obj, attr_name, default) if obj else default
        except Exception:
            return default
    
    def _safe_call_method(self, obj, method_name, *args, **kwargs):
        """安全調用對象方法"""
        try:
            if obj and hasattr(obj, method_name):
                method = getattr(obj, method_name)
                return method(*args, **kwargs)
            return None
        except Exception as e:
            logger.error(f"調用方法 {method_name} 時發生錯誤: {e}")
            return None
    
    def _is_dict_like(self, obj):
        """檢查對象是否類似字典"""
        return hasattr(obj, 'get') or isinstance(obj, dict)
    
    def _get_value(self, obj, key, default=None):
        """安全獲取值"""
        try:
            if self._is_dict_like(obj):
                return obj.get(key, default)
            else:
                return getattr(obj, key, default)
        except Exception:
            return default
    
    def render_trading_dashboard(self):
        """渲染交易儀表板主頁面"""
        st.title("📊 智能交易系統儀表板")
        
        # 顯示運行模式
        mode_indicator = "🟢 完整模式" if self.full_mode else "🟡 簡化模式"
        st.caption(f"運行模式: {mode_indicator}")
        
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
    
    def _render_overview_tab(self):
        """渲染總覽頁面"""
        st.header("📊 投資組合總覽")
        
        try:
            # 顯示系統狀態
            self._display_system_status()
            
            # 顯示績效指標
            self._display_performance_metrics()
            
            # 顯示當前持倉
            if st.checkbox("顯示當前持倉", value=True):
                self._display_current_holdings()
            
            # 顯示市場洞察
            self._display_market_insights()
            
        except Exception as e:
            st.error(f"渲染總覽頁面時發生錯誤: {str(e)}")
            logger.error(f"渲染總覽頁面錯誤: {e}")
    
    def _display_system_status(self):
        """顯示系統狀態"""
        st.subheader("系統狀態")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            recorder_status = "✅ 正常" if self.trade_recorder else "❌ 未載入"
            st.metric("交易記錄器", recorder_status)
        
        with col2:
            analyzer_status = "✅ 正常" if self.signal_analyzer else "❌ 未載入"
            st.metric("信號分析器", analyzer_status)
        
        with col3:
            engine_status = "✅ 正常" if self.auto_trading_engine else "❌ 未載入"
            st.metric("自動交易引擎", engine_status)
    
    def _display_performance_metrics(self):
        """顯示績效指標"""
        st.subheader("績效指標")
        
        try:
            if self.full_mode and self.trade_recorder:
                # 使用真實數據
                all_trades = self._safe_call_method(self.trade_recorder, 'get_all_trades') or []
            else:
                # 使用簡化模式數據
                all_trades = st.session_state.trades
            
            # 計算指標
            total_trades = len(all_trades)
            closed_trades = [t for t in all_trades if self._get_value(t, 'status') == TradeStatus.CLOSED]
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("總交易數", total_trades)
            
            with col2:
                total_pnl = 0
                for t in closed_trades:
                    pnl_value = self._get_value(t, 'realized_pnl', 0)
                    if pnl_value is not None:
                        try:
                            total_pnl += float(pnl_value)
                        except (ValueError, TypeError):
                            pass
                st.metric("總損益", f"${total_pnl:.2f}")
            
            with col3:
                if closed_trades:
                    winning_count = 0
                    for t in closed_trades:
                        pnl_value = self._get_value(t, 'realized_pnl', 0)
                        if pnl_value is not None:
                            try:
                                if float(pnl_value) > 0:
                                    winning_count += 1
                            except (ValueError, TypeError):
                                pass
                    win_rate = winning_count / len(closed_trades) * 100
                    st.metric("勝率", f"{win_rate:.1f}%")
                else:
                    st.metric("勝率", "0.0%")
            
            with col4:
                st.metric("平均回報", "計算中...")
                
        except Exception as e:
            st.error(f"顯示績效指標時發生錯誤: {str(e)}")
            logger.error(f"顯示績效指標錯誤: {e}")
    
    def _display_current_holdings(self):
        """顯示當前持倉"""
        st.subheader("當前持倉")
        
        try:
            if self.full_mode and self.trade_recorder:
                # 使用真實數據
                open_trades = self._safe_call_method(self.trade_recorder, 'get_open_trades') or []
            else:
                # 使用簡化模式數據
                open_trades = [t for t in st.session_state.trades if self._get_value(t, 'status') == TradeStatus.OPEN]
            
            if open_trades:
                holdings_data = []
                for trade in open_trades:
                    current_price = self._get_mock_current_price(self._get_value(trade, 'stock_code', ''))
                    holdings_data.append({
                        '股票代碼': self._get_value(trade, 'stock_code', ''),
                        '交易類型': self._get_value(trade, 'trade_type', ''),
                        '進入價格': f"${self._get_value(trade, 'entry_price', 0):.2f}",
                        '當前價格': f"${current_price:.2f}",
                        '數量': self._get_value(trade, 'quantity', 0),
                        '未實現損益': f"${self._get_value(trade, 'unrealized_pnl', 0):.2f}",
                        '進入日期': self._get_value(trade, 'entry_time', 'N/A'),
                        '信號類型': self._get_value(trade, 'signal_type', '')
                    })
                
                df = pd.DataFrame(holdings_data)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("目前沒有持倉")
                
        except Exception as e:
            st.error(f"載入持倉數據時發生錯誤: {str(e)}")
            logger.error(f"顯示持倉錯誤: {e}")
    
    def _display_market_insights(self):
        """顯示市場洞察"""
        st.subheader("市場洞察")
        
        try:
            if self.signal_analyzer:
                # 使用真實的市場洞察
                insights = self._safe_call_method(self.signal_analyzer, 'get_market_insights') or []
                if insights:
                    for insight in insights:
                        st.info(f"💡 {insight}")
                else:
                    st.info("暫無市場洞察")
            else:
                # 顯示模擬洞察
                mock_insights = [
                    "技術指標顯示大盤可能進入調整期",
                    "DCF分析發現多支潛力股票",
                    "建議關注科技板塊的投資機會"
                ]
                for insight in mock_insights:
                    st.info(f"💡 {insight}")
                    
        except Exception as e:
            st.error(f"載入市場洞察時發生錯誤: {str(e)}")
            logger.error(f"顯示市場洞察錯誤: {e}")
    
    def _get_mock_current_price(self, stock_code):
        """獲取模擬的當前價格"""
        try:
            # 簡單的模擬價格生成
            base_price = hash(stock_code) % 100 + 10
            variation = random.uniform(-5, 5)
            return max(base_price + variation, 1.0)
        except Exception:
            return 50.0
    
    def _render_trade_records_tab(self):
        """渲染交易記錄頁面"""
        st.header("📝 交易記錄管理")
        
        try:
            # 添加新交易表單
            if st.checkbox("添加新交易"):
                self._render_add_trade_form()
            
            # 篩選選項
            col1, col2, col3 = st.columns(3)
            
            with col1:
                status_filter = st.selectbox("篩選狀態", 
                                           ["全部", TradeStatus.OPEN, TradeStatus.CLOSED, TradeStatus.PARTIAL])
            
            with col2:
                signal_filter = st.selectbox("篩選信號", 
                                           ["全部", SignalType.DCF_BUY, SignalType.DCF_SELL, 
                                            SignalType.TECHNICAL_BUY, SignalType.TECHNICAL_SELL, SignalType.MANUAL])
            
            with col3:
                date_range = st.date_input("日期範圍", [datetime.now() - timedelta(days=30), datetime.now()])
            
            # 顯示交易記錄
            self._display_filtered_trades(status_filter, signal_filter, date_range)
            
        except Exception as e:
            st.error(f"渲染交易記錄頁面時發生錯誤: {str(e)}")
            logger.error(f"渲染交易記錄錯誤: {e}")
    
    def _render_add_trade_form(self):
        """渲染添加交易表單"""
        st.subheader("添加新交易")
        
        with st.form("add_trade_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                stock_code = st.text_input("股票代碼")
                trade_type = st.selectbox("交易類型", [TradeType.BUY, TradeType.SELL])
                quantity = st.number_input("數量", min_value=1, value=100)
            
            with col2:
                entry_price = st.number_input("價格", min_value=0.01, value=10.0, step=0.01)
                signal_type = st.selectbox("信號類型", 
                                         [SignalType.MANUAL, SignalType.DCF_BUY, SignalType.DCF_SELL,
                                          SignalType.TECHNICAL_BUY, SignalType.TECHNICAL_SELL])
                notes = st.text_area("備註")
            
            if st.form_submit_button("添加交易"):
                try:
                    trade_data = {
                        'id': str(uuid.uuid4()),
                        'stock_code': stock_code,
                        'trade_type': trade_type,
                        'quantity': quantity,
                        'entry_price': entry_price,
                        'signal_type': signal_type,
                        'notes': notes,
                        'entry_time': datetime.now().isoformat(),
                        'status': TradeStatus.OPEN,
                        'realized_pnl': 0,
                        'unrealized_pnl': 0
                    }
                    
                    if self.full_mode and self.trade_recorder:
                        # 使用真實的交易記錄器
                        self._safe_call_method(self.trade_recorder, 'add_trade', trade_data)
                    else:
                        # 添加到簡化模式數據
                        st.session_state.trades.append(trade_data)
                    
                    st.success(f"成功添加交易: {stock_code}")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"添加交易失敗: {str(e)}")
                    logger.error(f"添加交易錯誤: {e}")
    
    def _display_filtered_trades(self, status_filter, signal_filter, date_range):
        """顯示篩選後的交易"""
        try:
            if self.full_mode and self.trade_recorder:
                trades = self._filter_full_trades(status_filter, signal_filter, date_range)
            else:
                trades = self._filter_simple_trades(status_filter, signal_filter, date_range)
            
            if trades:
                # 轉換為DataFrame顯示
                trades_data = []
                for trade in trades:
                    trades_data.append({
                        'ID': self._get_value(trade, 'id', ''),
                        '股票代碼': self._get_value(trade, 'stock_code', ''),
                        '類型': self._get_value(trade, 'trade_type', ''),
                        '數量': self._get_value(trade, 'quantity', 0),
                        '價格': f"${self._get_value(trade, 'entry_price', 0):.2f}",
                        '狀態': self._get_value(trade, 'status', ''),
                        '信號': self._get_value(trade, 'signal_type', ''),
                        '時間': self._get_value(trade, 'entry_time', ''),
                        '損益': f"${self._get_value(trade, 'realized_pnl', 0):.2f}"
                    })
                
                df = pd.DataFrame(trades_data)
                st.dataframe(df, use_container_width=True)
                
                # 顯示統計信息
                st.info(f"找到 {len(trades)} 筆交易記錄")
            else:
                st.info("沒有找到符合條件的交易記錄")
                
        except Exception as e:
            st.error(f"顯示交易記錄時發生錯誤: {str(e)}")
            logger.error(f"顯示交易記錄錯誤: {e}")
    
    def _filter_full_trades(self, status_filter, signal_filter, date_range):
        """使用完整TradeRecorder篩選"""
        try:
            all_trades = self._safe_call_method(self.trade_recorder, 'get_all_trades') or []
            filtered = all_trades
            
            # 狀態篩選
            if status_filter != "全部":
                filtered = [t for t in filtered if self._get_value(t, 'status') == status_filter]
            
            # 信號篩選
            if signal_filter != "全部":
                filtered = [t for t in filtered if self._get_value(t, 'signal_type') == signal_filter]
            
            # 日期篩選
            if date_range and len(date_range) == 2:
                start_date, end_date = date_range
                filtered_by_date = []
                for t in filtered:
                    entry_time = self._get_value(t, 'entry_time', '2000-01-01')
                    if entry_time:
                        try:
                            trade_date = datetime.fromisoformat(str(entry_time)).date()
                            if start_date <= trade_date <= end_date:
                                filtered_by_date.append(t)
                        except (ValueError, TypeError):
                            pass
                filtered = filtered_by_date
            
            return filtered
            
        except Exception as e:
            logger.error(f"篩選完整交易記錄錯誤: {e}")
            return []
    
    def _filter_simple_trades(self, status_filter, signal_filter, date_range):
        """篩選簡化模式交易"""
        try:
            trades = st.session_state.trades
            filtered = trades
            
            # 狀態篩選
            if status_filter != "全部":
                filtered = [t for t in filtered if t.get('status') == status_filter]
            
            # 信號篩選
            if signal_filter != "全部":
                filtered = [t for t in filtered if t.get('signal_type') == signal_filter]
            
            # 日期篩選
            if date_range and len(date_range) == 2:
                start_date, end_date = date_range
                filtered_by_date = []
                for t in filtered:
                    entry_time = t.get('entry_time', '2000-01-01')
                    if entry_time:
                        try:
                            trade_date = datetime.fromisoformat(str(entry_time)).date()
                            if start_date <= trade_date <= end_date:
                                filtered_by_date.append(t)
                        except (ValueError, TypeError):
                            pass
                filtered = filtered_by_date
            
            return filtered
            
        except Exception as e:
            logger.error(f"篩選簡化交易記錄錯誤: {e}")
            return []
    
    def _render_ai_recommendations_tab(self):
        """渲染AI建議頁面"""
        st.header("🤖 AI投資建議")
        
        try:
            # 生成建議按鈕
            if st.button("生成新建議"):
                self._generate_ai_recommendations()
            
            # 顯示建議列表
            self._display_ai_recommendations()
            
        except Exception as e:
            st.error(f"渲染AI建議頁面時發生錯誤: {str(e)}")
            logger.error(f"渲染AI建議錯誤: {e}")
    
    def _generate_ai_recommendations(self):
        """生成AI建議"""
        try:
            if self.signal_analyzer:
                # 使用真實的信號分析器
                recommendations = self._safe_call_method(self.signal_analyzer, 'generate_recommendations') or []
                if recommendations:
                    st.session_state.ai_suggestions.extend(recommendations)
                    st.success(f"生成了 {len(recommendations)} 個新建議")
            else:
                # 生成模擬建議
                mock_recommendations = [
                    {
                        'id': str(uuid.uuid4()),
                        'stock_code': f"股票{random.randint(1000, 9999)}",
                        'recommendation': random.choice(['買入', '賣出', '持有']),
                        'confidence': random.uniform(0.6, 0.95),
                        'reason': "基於DCF分析和技術指標",
                        'timestamp': datetime.now().isoformat()
                    }
                    for _ in range(3)
                ]
                st.session_state.ai_suggestions.extend(mock_recommendations)
                st.success(f"生成了 {len(mock_recommendations)} 個新建議")
                
        except Exception as e:
            st.error(f"生成AI建議失敗: {str(e)}")
            logger.error(f"生成AI建議錯誤: {e}")
    
    def _display_ai_recommendations(self):
        """顯示AI建議"""
        try:
            recommendations = st.session_state.ai_suggestions
            
            if recommendations:
                for i, rec in enumerate(reversed(recommendations[-10:])):  # 顯示最新10個
                    with st.expander(f"建議 {i+1}: {rec.get('stock_code', 'N/A')} - {rec.get('recommendation', 'N/A')}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**股票代碼:** {rec.get('stock_code', 'N/A')}")
                            st.write(f"**建議:** {rec.get('recommendation', 'N/A')}")
                            st.write(f"**信心度:** {rec.get('confidence', 0):.2%}")
                        
                        with col2:
                            st.write(f"**理由:** {rec.get('reason', 'N/A')}")
                            st.write(f"**時間:** {rec.get('timestamp', 'N/A')}")
            else:
                st.info("暫無AI建議，點擊上方按鈕生成新建議")
                
        except Exception as e:
            st.error(f"顯示AI建議時發生錯誤: {str(e)}")
            logger.error(f"顯示AI建議錯誤: {e}")
    
    def _render_signal_scanning_tab(self):
        """渲染信號掃描頁面"""
        st.header("🔍 信號掃描")
        
        try:
            # 掃描控制
            col1, col2 = st.columns(2)
            
            with col1:
                watchlist = st.text_area("監控清單（每行一個股票代碼）", 
                                       value="AAPL\nTSLA\nMSFT\nGOOGL")
            
            with col2:
                scan_type = st.selectbox("掃描類型", ["DCF信號", "技術信號", "綜合信號"])
                
                if st.button("開始掃描"):
                    self._perform_signal_scan(watchlist, scan_type)
            
            # 自動交易控制
            if self.auto_trading_engine:
                self._render_auto_trading_controls(watchlist)
            
            # 信號參數設定
            self._render_signal_parameters()
            
        except Exception as e:
            st.error(f"渲染信號掃描頁面時發生錯誤: {str(e)}")
            logger.error(f"渲染信號掃描錯誤: {e}")
    
    def _perform_signal_scan(self, watchlist_text, scan_type):
        """執行信號掃描"""
        try:
            watchlist = [code.strip() for code in watchlist_text.split('\n') if code.strip()]
            
            if self.signal_analyzer:
                # 使用真實的信號分析器
                scan_results = self._safe_call_method(self.signal_analyzer, 'scan_signals', watchlist, scan_type) or []
            else:
                # 生成模擬掃描結果
                scan_results = []
                for code in watchlist:
                    if random.random() > 0.7:  # 30%機率產生信號
                        signal = {
                            'stock_code': code,
                            'signal_type': random.choice([SignalType.DCF_BUY, SignalType.DCF_SELL, 
                                                        SignalType.TECHNICAL_BUY, SignalType.TECHNICAL_SELL]),
                            'strength': random.uniform(0.5, 0.9),
                            'reasoning': f"基於{scan_type}分析",
                            'timestamp': datetime.now().isoformat()
                        }
                        scan_results.append(signal)
            
            if scan_results:
                st.success(f"掃描完成，發現 {len(scan_results)} 個信號")
                
                # 顯示掃描結果
                for signal in scan_results:
                    with st.expander(f"信號: {signal.get('stock_code')} - {signal.get('signal_type')}"):
                        st.write(f"**強度:** {signal.get('strength', 0):.2%}")
                        st.write(f"**理由:** {signal.get('reasoning', 'N/A')}")
                        st.write(f"**時間:** {signal.get('timestamp', 'N/A')}")
                
                # 保存掃描結果
                st.session_state.signal_scan_results = scan_results
            else:
                st.info("未發現任何信號")
                
        except Exception as e:
            st.error(f"信號掃描失敗: {str(e)}")
            logger.error(f"信號掃描錯誤: {e}")
    
    def _render_auto_trading_controls(self, watchlist_text):
        """渲染自動交易控制"""
        st.subheader("自動交易控制")
        
        try:
            col1, col2 = st.columns(2)
            
            with col1:
                auto_enabled_value = self._safe_get_attr(self.auto_trading_engine, 'auto_trade_enabled', False)
                if auto_enabled_value is None:
                    auto_enabled_value = False
                auto_enabled = st.checkbox("啟用自動交易", value=bool(auto_enabled_value))
                
                if auto_enabled != auto_enabled_value:
                    self._safe_call_method(self.auto_trading_engine, 'set_auto_trade_enabled', auto_enabled)
            
            with col2:
                if st.button("執行日度掃描"):
                    watchlist = [code.strip() for code in watchlist_text.split('\n') if code.strip()]
                    result = self._safe_call_method(self.auto_trading_engine, 'execute_daily_scan', watchlist)
                    if result:
                        st.success("日度掃描執行完成")
                    else:
                        st.warning("日度掃描執行失敗")
            
            # 顯示自動交易狀態
            if auto_enabled:
                st.info("🟢 自動交易已啟用")
            else:
                st.info("🔴 自動交易已停用")
                
        except Exception as e:
            st.error(f"渲染自動交易控制時發生錯誤: {str(e)}")
            logger.error(f"渲染自動交易控制錯誤: {e}")
    
    def _render_signal_parameters(self):
        """渲染信號參數設定"""
        st.subheader("信號參數設定")
        
        try:
            with st.expander("DCF參數"):
                dcf_threshold = st.slider("DCF閾值", 0.1, 0.5, 0.2, 0.05)
                dcf_confidence = st.slider("DCF信心度", 0.5, 0.95, 0.7, 0.05)
            
            with st.expander("技術分析參數"):
                rsi_period = st.number_input("RSI週期", 5, 50, 14)
                ma_period = st.number_input("移動平均週期", 5, 200, 20)
            
            if st.button("保存參數"):
                parameters = {
                    'dcf_threshold': dcf_threshold,
                    'dcf_confidence': dcf_confidence,
                    'rsi_period': rsi_period,
                    'ma_period': ma_period
                }
                
                if self.signal_analyzer:
                    self._safe_call_method(self.signal_analyzer, 'update_parameters', parameters)
                    st.success("參數已保存")
                else:
                    st.session_state.signal_parameters = parameters
                    st.success("參數已保存到session")
                    
        except Exception as e:
            st.error(f"設定信號參數時發生錯誤: {str(e)}")
            logger.error(f"設定信號參數錯誤: {e}")
    
    def _render_settings_tab(self):
        """渲染設定頁面"""
        st.header("⚙️ 系統設定")
        
        try:
            # 系統配置
            st.subheader("系統配置")
            
            col1, col2 = st.columns(2)
            
            with col1:
                debug_mode = st.checkbox("除錯模式", value=False)
                auto_refresh = st.checkbox("自動刷新", value=True)
                refresh_interval = st.number_input("刷新間隔（秒）", 1, 300, 30)
            
            with col2:
                max_trades = st.number_input("最大交易數", 1, 1000, 100)
                risk_limit = st.number_input("風險限制（%）", 1, 50, 10)
            
            # 通知設定
            st.subheader("通知設定")
            
            email_notifications = st.checkbox("郵件通知", value=False)
            if email_notifications:
                email_address = st.text_input("郵件地址")
            
            telegram_notifications = st.checkbox("Telegram通知", value=False)
            if telegram_notifications:
                telegram_token = st.text_input("Telegram Token", type="password")
            
            # 數據管理
            st.subheader("數據管理")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("匯出數據"):
                    self._export_data()
            
            with col2:
                if st.button("清除快取"):
                    self._clear_cache()
            
            with col3:
                if st.button("重置系統"):
                    self._reset_system()
            
            # 保存設定
            if st.button("保存設定"):
                settings = {
                    'debug_mode': debug_mode,
                    'auto_refresh': auto_refresh,
                    'refresh_interval': refresh_interval,
                    'max_trades': max_trades,
                    'risk_limit': risk_limit,
                    'email_notifications': email_notifications,
                    'telegram_notifications': telegram_notifications
                }
                
                st.session_state.system_settings = settings
                st.success("設定已保存")
                
        except Exception as e:
            st.error(f"渲染設定頁面時發生錯誤: {str(e)}")
            logger.error(f"渲染設定錯誤: {e}")
    
    def _export_data(self):
        """匯出數據"""
        try:
            if self.full_mode and self.trade_recorder:
                # 匯出真實數據
                data = self._safe_call_method(self.trade_recorder, 'export_data')
            else:
                # 匯出簡化模式數據
                data = {
                    'trades': st.session_state.trades,
                    'ai_suggestions': st.session_state.ai_suggestions,
                    'signal_scan_results': st.session_state.get('signal_scan_results', [])
                }
            
            if data:
                st.download_button(
                    label="下載數據",
                    data=str(data),
                    file_name=f"trading_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
                st.success("數據匯出準備完成")
            else:
                st.warning("沒有可匯出的數據")
                
        except Exception as e:
            st.error(f"匯出數據失敗: {str(e)}")
            logger.error(f"匯出數據錯誤: {e}")
    
    def _clear_cache(self):
        """清除快取"""
        try:
            # 清除Streamlit快取
            st.cache_data.clear()
            
            # 清除session狀態中的暫時數據
            if 'signal_scan_results' in st.session_state:
                del st.session_state.signal_scan_results
            
            st.success("快取已清除")
            
        except Exception as e:
            st.error(f"清除快取失敗: {str(e)}")
            logger.error(f"清除快取錯誤: {e}")
    
    def _reset_system(self):
        """重置系統"""
        try:
            # 清除所有session數據
            keys_to_clear = ['trades', 'ai_suggestions', 'signal_scan_results', 'system_settings']
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            
            # 重新初始化
            self._initialize_simple_mode_data()
            
            st.success("系統已重置")
            st.rerun()
            
        except Exception as e:
            st.error(f"重置系統失敗: {str(e)}")
            logger.error(f"重置系統錯誤: {e}")

# 工廠函數
def create_trading_ui(trade_recorder=None, signal_analyzer=None, auto_trading_engine=None):
    """創建交易系統UI實例"""
    return TradingSystemUI(trade_recorder, signal_analyzer, auto_trading_engine)
