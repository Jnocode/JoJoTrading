"""
交易系統UI組件
用於在Streamlit應用中展示交易記錄、AI建議和績效報告
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from .trade_recorder import TradeRecorder, TradeEntry, TradeType, TradeStatus, SignalType
from .ai_advisor import AITradingAdvisor, TradingSignal, create_ai_advisor
from .signal_generator import SignalGenerator, AutoTradingEngine, create_signal_generator, create_auto_trading_engine


class TradingSystemUI:
    """交易系統UI管理器"""
    
    def __init__(self):
        # 初始化交易系統組件
        if 'trade_recorder' not in st.session_state:
            st.session_state.trade_recorder = TradeRecorder()
        
        if 'ai_advisor' not in st.session_state:
            st.session_state.ai_advisor = create_ai_advisor(st.session_state.trade_recorder)
        
        if 'signal_generator' not in st.session_state:
            st.session_state.signal_generator = create_signal_generator(
                st.session_state.trade_recorder, 
                st.session_state.ai_advisor
            )
        
        if 'auto_trading_engine' not in st.session_state:
            st.session_state.auto_trading_engine = create_auto_trading_engine(
                st.session_state.trade_recorder,
                st.session_state.signal_generator
            )
        
        self.trade_recorder = st.session_state.trade_recorder
        self.ai_advisor = st.session_state.ai_advisor
        self.signal_generator = st.session_state.signal_generator
        self.auto_trading_engine = st.session_state.auto_trading_engine
    
    def render_trading_dashboard(self):
        """渲染交易儀表板主頁面"""
        st.title("📊 智能交易系統儀表板")
        
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
        
        # 績效指標
        performance = self.trade_recorder.calculate_portfolio_performance()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("總交易數", performance['total_trades'])
        
        with col2:
            total_pnl = performance['total_pnl']
            st.metric("總損益", f"${total_pnl:.2f}", 
                     delta=f"{total_pnl:.2f}" if total_pnl != 0 else None)
        
        with col3:
            win_rate = performance['win_rate']
            st.metric("勝率", f"{win_rate:.1f}%", 
                     delta=f"{win_rate-50:.1f}%" if win_rate != 0 else None)
        
        with col4:
            avg_return = performance['avg_return']
            st.metric("平均回報", f"{avg_return:.2f}%", 
                     delta=f"{avg_return:.2f}%" if avg_return != 0 else None)
        
        # 開倉位置概況
        st.subheader("💼 當前持倉")
        open_trades = self.trade_recorder.get_open_trades()
        
        if open_trades:
            # 更新未實現損益
            for trade in open_trades:
                current_price = self._get_mock_current_price(trade.stock_code)
                self.trade_recorder.update_unrealized_pnl(trade.stock_code, current_price)
            
            # 顯示持倉表格
            holdings_data = []
            for trade in open_trades:
                current_price = self._get_mock_current_price(trade.stock_code)
                holdings_data.append({
                    '股票代碼': trade.stock_code,
                    '交易類型': trade.trade_type.value,
                    '進入價格': f"${trade.entry_price:.2f}",
                    '當前價格': f"${current_price:.2f}",
                    '數量': trade.quantity,
                    '未實現損益': f"${trade.unrealized_pnl:.2f}" if trade.unrealized_pnl else "N/A",
                    '進入日期': trade.entry_time.strftime('%Y-%m-%d'),
                    '信號類型': trade.signal_type.value
                })
            
            df_holdings = pd.DataFrame(holdings_data)
            st.dataframe(df_holdings, use_container_width=True)
            
            # 持倉分析圖表
            self._render_holdings_chart(open_trades)
        else:
            st.info("🔍 目前沒有開倉位置")
        
        # 最新市場洞察
        st.subheader("🎯 市場洞察")
        market_insight = self.ai_advisor.generate_market_insight()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**市場情緒:**", market_insight['market_sentiment'])
            st.write("**最佳策略:**", market_insight['recommendations']['top_strategy'])
        
        with col2:
            if market_insight['recommendations']['risk_warning']:
                st.warning("⚠️ **風險警告:**")
                for warning in market_insight['recommendations']['risk_warning']:
                    st.write(f"• {warning}")
    
    def _render_trade_records_tab(self):
        """渲染交易記錄頁面"""
        st.header("📝 交易記錄管理")
        
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
            signal_filter = st.selectbox(
                "信號類型",
                options=["全部"] + [signal.value for signal in SignalType],
                index=0
            )
        
        with col3:
            date_range = st.date_input(
                "日期範圍",
                value=(datetime.now() - timedelta(days=30), datetime.now()),
                max_value=datetime.now()
            )
        
        # 顯示篩選後的交易記錄
        filtered_trades = self._filter_trades(status_filter, signal_filter, date_range)
        
        if filtered_trades:
            # 交易記錄表格
            trades_data = []
            for trade in filtered_trades:
                trades_data.append({
                    '交易ID': trade.trade_id[:8],
                    '股票代碼': trade.stock_code,
                    '類型': trade.trade_type.value,
                    '進入價格': f"${trade.entry_price:.2f}",
                    '出場價格': f"${trade.exit_price:.2f}" if trade.exit_price else "未平倉",
                    '數量': trade.quantity,
                    '實現損益': f"${trade.realized_pnl:.2f}" if trade.realized_pnl else "未實現",
                    '回報率': f"{trade.return_percentage:.2f}%" if trade.return_percentage else "N/A",
                    '狀態': trade.status.value,
                    '信號': trade.signal_type.value,
                    '進入日期': trade.entry_time.strftime('%Y-%m-%d %H:%M')
                })
            
            df_trades = pd.DataFrame(trades_data)
            st.dataframe(df_trades, use_container_width=True)
            
            # 交易統計
            self._render_trade_statistics(filtered_trades)
            
            # 績效圖表
            self._render_performance_charts(filtered_trades)
        else:
            st.info("🔍 沒有符合篩選條件的交易記錄")
    
    def _render_ai_recommendations_tab(self):
        """渲染AI建議頁面"""
        st.header("🤖 AI智能建議")
        
        # 輸入股票進行分析
        st.subheader("📊 股票分析")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            stock_code = st.text_input("輸入股票代碼", placeholder="例如: 2330")
        
        with col2:
            if st.button("🔍 分析股票", type="primary"):
                if stock_code:
                    self._analyze_stock_with_ai(stock_code)
        
        # 投資組合建議
        st.subheader("📈 投資組合建議")
        
        if st.button("🎯 生成投資組合建議"):
            self._generate_portfolio_recommendations()
        
        # 顯示現有信號
        self._display_existing_signals()
    
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
        
        auto_enabled = st.checkbox(
            "啟用自動交易",
            value=self.auto_trading_engine.auto_trade_enabled,
            help="啟用後系統將自動執行交易信號"
        )
        
        if auto_enabled != self.auto_trading_engine.auto_trade_enabled:
            self.auto_trading_engine.enable_auto_trading(auto_enabled)
            st.success(f"自動交易已{'啟用' if auto_enabled else '停用'}")
        
        if auto_enabled:
            if st.button("▶️ 執行每日掃描"):
                with st.spinner("執行自動交易掃描..."):
                    result = self.auto_trading_engine.execute_daily_scan(watchlist)
                    st.json(result)
    
    def _render_settings_tab(self):
        """渲染設定頁面"""
        st.header("⚙️ 系統設定")
        
        # AI建議參數
        st.subheader("🤖 AI建議參數")
        
        col1, col2 = st.columns(2)
        
        with col1:
            dcf_buy_threshold = st.slider(
                "DCF買入折價門檻",
                min_value=0.05,
                max_value=0.30,
                value=self.signal_generator.dcf_buy_threshold,
                step=0.01,
                format="%.2f",
                help="DCF估值低於市價的最小折價要求"
            )
            
            confidence_threshold = st.slider(
                "最低信心度要求",
                min_value=30,
                max_value=90,
                value=self.signal_generator.confidence_threshold,
                step=5,
                help="交易信號的最低信心度要求"
            )
        
        with col2:
            dcf_sell_threshold = st.slider(
                "DCF賣出溢價門檻",
                min_value=-0.30,
                max_value=-0.05,
                value=self.signal_generator.dcf_sell_threshold,
                step=0.01,
                format="%.2f",
                help="DCF估值高於市價的最小溢價要求"
            )
            
            quality_threshold = st.slider(
                "最低數據品質要求",
                min_value=30,
                max_value=80,
                value=self.signal_generator.quality_min_threshold,
                step=5,
                help="股票數據的最低品質要求"
            )
        
        # 更新參數
        if st.button("💾 儲存設定"):
            self.signal_generator.dcf_buy_threshold = dcf_buy_threshold
            self.signal_generator.dcf_sell_threshold = dcf_sell_threshold
            self.signal_generator.confidence_threshold = confidence_threshold
            self.signal_generator.quality_min_threshold = quality_threshold
            st.success("✅ 設定已儲存")
        
        # 資料管理
        st.subheader("📁 資料管理")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📥 匯出交易記錄"):
                self._export_trade_records()
        
        with col2:
            if st.button("🔄 重新載入記錄"):
                self.trade_recorder.load_trades()
                st.success("✅ 交易記錄已重新載入")
        
        with col3:
            if st.button("🗑️ 清除所有記錄", type="secondary"):
                if st.confirm("確定要清除所有交易記錄嗎？此操作無法復原。"):
                    self.trade_recorder.trades.clear()
                    self.trade_recorder.save_trades()
                    st.success("✅ 所有記錄已清除")
    
    def _render_add_trade_form(self):
        """渲染新增交易表單"""
        with st.form("add_trade_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                stock_code = st.text_input("股票代碼*", placeholder="例如: 2330")
                trade_type = st.selectbox("交易類型*", options=[t.value for t in TradeType])
                entry_price = st.number_input("進入價格*", min_value=0.01, step=0.01)
                quantity = st.number_input("數量*", min_value=1, step=1)
            
            with col2:
                signal_type = st.selectbox("信號類型", options=[s.value for s in SignalType])
                dcf_value = st.number_input("DCF內在價值", min_value=0.0, step=0.01)
                notes = st.text_area("備註", height=100)
            
            submitted = st.form_submit_button("➕ 新增交易記錄")
            
            if submitted:
                if stock_code and entry_price > 0 and quantity > 0:
                    trade = TradeEntry(
                        stock_code=stock_code,
                        stock_name=f"{stock_code}公司",
                        trade_type=TradeType(trade_type),
                        entry_price=entry_price,
                        quantity=quantity,
                        signal_type=SignalType(signal_type),
                        dcf_intrinsic_value=dcf_value if dcf_value > 0 else None,
                        notes=notes
                    )
                    
                    trade_id = self.trade_recorder.add_trade(trade)
                    st.success(f"✅ 交易記錄已新增 (ID: {trade_id[:8]})")
                else:
                    st.error("❌ 請填寫所有必填欄位")
    
    def _filter_trades(self, status_filter: str, signal_filter: str, date_range) -> List[TradeEntry]:
        """篩選交易記錄"""
        trades = self.trade_recorder.trades.copy()
        
        # 狀態篩選
        if status_filter != "全部":
            status_map = {
                "開倉": TradeStatus.OPEN,
                "平倉": TradeStatus.CLOSED,
                "部分平倉": TradeStatus.PARTIAL
            }
            trades = [t for t in trades if t.status == status_map[status_filter]]
        
        # 信號類型篩選
        if signal_filter != "全部":
            trades = [t for t in trades if t.signal_type.value == signal_filter]
        
        # 日期篩選
        if len(date_range) == 2:
            start_date, end_date = date_range
            start_datetime = datetime.combine(start_date, datetime.min.time())
            end_datetime = datetime.combine(end_date, datetime.max.time())
            trades = [t for t in trades if start_datetime <= t.entry_time <= end_datetime]
        
        return trades
    
    def _get_mock_current_price(self, stock_code: str) -> float:
        """獲取模擬當前價格"""
        import random
        base_price = hash(stock_code) % 200 + 50
        volatility = random.uniform(-0.05, 0.05)
        return base_price * (1 + volatility)
    
    def _render_holdings_chart(self, open_trades: List[TradeEntry]):
        """渲染持倉分析圖表"""
        if not open_trades:
            return
        
        # 按股票分組
        holdings_summary = {}
        for trade in open_trades:
            code = trade.stock_code
            if code not in holdings_summary:
                holdings_summary[code] = {
                    'quantity': 0,
                    'total_cost': 0,
                    'unrealized_pnl': 0
                }
            
            holdings_summary[code]['quantity'] += trade.quantity
            holdings_summary[code]['total_cost'] += trade.entry_price * trade.quantity
            holdings_summary[code]['unrealized_pnl'] += trade.unrealized_pnl or 0
        
        # 創建圖表數據
        stocks = list(holdings_summary.keys())
        unrealized_pnl = [holdings_summary[stock]['unrealized_pnl'] for stock in stocks]
        
        # 損益圖表
        fig = go.Figure(data=[
            go.Bar(
                x=stocks,
                y=unrealized_pnl,
                marker_color=['green' if pnl >= 0 else 'red' for pnl in unrealized_pnl],
                text=[f"${pnl:.2f}" for pnl in unrealized_pnl],
                textposition='auto'
            )
        ])
        
        fig.update_layout(
            title="持倉未實現損益",
            xaxis_title="股票代碼",
            yaxis_title="未實現損益 ($)",
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _analyze_stock_with_ai(self, stock_code: str):
        """使用AI分析股票"""
        # 獲取模擬數據
        current_price = self._get_mock_current_price(stock_code)
        mock_data = {
            'stock_code': stock_code,
            'stock_name': f"{stock_code}公司",
            'current_price': current_price,
            'intrinsic_value_per_share': current_price * (0.8 + 0.6 * hash(stock_code) % 100 / 100),
            'pe_ratio': 15 + (hash(stock_code) % 20),
            'pb_ratio': 0.8 + (hash(stock_code) % 30) / 10,
            'roe': 0.05 + (hash(stock_code) % 20) / 100,
            'debt_ratio': 0.2 + (hash(stock_code) % 50) / 100,
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
            st.write(f"**DCF內在價值:** ${analysis.dcf_intrinsic_value:.2f}")
            st.write(f"**折價/溢價:** {analysis.dcf_discount:.1%}")
            st.write(f"**PE比率:** {analysis.pe_ratio:.1f}")
            st.write(f"**ROE:** {analysis.roe:.1%}")
            st.write(f"**負債比率:** {analysis.debt_ratio:.1%}")
        
        with col2:
            st.subheader("📈 評分分析")
            st.progress(analysis.fundamental_score / 100, text=f"基本面評分: {analysis.fundamental_score:.0f}/100")
            st.progress(analysis.technical_score / 100, text=f"技術面評分: {analysis.technical_score:.0f}/100")
            st.progress(analysis.overall_score / 100, text=f"綜合評分: {analysis.overall_score:.0f}/100")
        
        # 顯示交易信號
        if signal:
            st.success(f"🎯 **AI建議:** {signal.action.value}")
            st.write(f"**信心度:** {signal.confidence:.0f}%")
            st.write(f"**目標價格:** ${signal.target_price:.2f}")
            st.write(f"**風險等級:** {signal.risk_level}")
            st.write(f"**建議理由:** {signal.reasoning}")
            
            if signal.stop_loss:
                st.write(f"**建議停損:** ${signal.stop_loss:.2f}")
        else:
            st.info("💡 目前沒有明確的交易信號")
    
    def _scan_entry_signals(self, watchlist: List[str]):
        """掃描進場信號"""
        if not watchlist:
            st.warning("請先設定監視列表")
            return
        
        entry_signals = self.signal_generator.generate_entry_signals(watchlist)
        
        if entry_signals:
            st.success(f"🎯 發現 {len(entry_signals)} 個進場信號")
            
            for signal_data in entry_signals[:5]:  # 顯示前5個
                signal = signal_data['signal']
                with st.expander(f"📈 {signal.stock_code} - {signal.action.value} (信心度: {signal.confidence:.0f}%)"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**目標價格:** ${signal.target_price:.2f}")
                        st.write(f"**風險等級:** {signal.risk_level}")
                        st.write(f"**優先級:** {signal_data['priority']:.2f}")
                    
                    with col2:
                        st.write(f"**建議倉位:** {signal_data['suggested_position_size']:.1%}")
                        st.write(f"**信號類型:** {signal.signal_type.value}")
                    
                    st.write(f"**理由:** {signal.reasoning}")
        else:
            st.info("🔍 目前沒有發現進場信號")
    
    def _scan_exit_signals(self):
        """掃描出場信號"""
        exit_signals = self.signal_generator.generate_exit_signals()
        
        if exit_signals:
            st.warning(f"🚪 發現 {len(exit_signals)} 個出場信號")
            
            for signal in exit_signals:
                with st.expander(f"🔄 {signal['stock_code']} - {signal['exit_reason']} (緊急度: {signal['urgency']}/10)"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**進入價格:** ${signal['entry_price']:.2f}")
                        st.write(f"**當前價格:** ${signal['current_price']:.2f}")
                    
                    with col2:
                        st.write(f"**未實現損益:** ${signal['unrealized_pnl']:.2f}")
                        st.write(f"**出場理由:** {signal['exit_reason']}")
                    
                    if st.button(f"✅ 執行出場 - {signal['stock_code']}", key=f"exit_{signal['trade_id']}"):
                        success = self.trade_recorder.close_trade(
                            signal['trade_id'], 
                            signal['current_price']
                        )
                        if success:
                            st.success("✅ 交易已平倉")
                            st.rerun()
        else:
            st.info("✅ 目前沒有需要出場的持倉")
    
    def _export_trade_records(self):
        """匯出交易記錄"""
        df = self.trade_recorder.to_dataframe()
        if not df.empty:
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 下載CSV檔案",
                data=csv,
                file_name=f"trade_records_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("沒有交易記錄可匯出")


# 主要UI函數
def render_trading_system():
    """渲染交易系統完整UI"""
    trading_ui = TradingSystemUI()
    trading_ui.render_trading_dashboard()
