import streamlit as st
import pandas as pd
import yfinance as yf
import json
import numpy as np
from pathlib import Path
import sys

# Core imports
from jojo_trading.analysis.patterns import PatternRecognizer

# 定義快取函式 (TTL 設為 12 小時，避免同日內重複下載)
@st.cache_data(ttl=43200, show_spinner=False)
def fetch_stock_history_cached(ticker: str):
    try:
        df = yf.download(ticker, period="6mo", interval="1d", progress=False)
        return df
    except Exception as e:
        return pd.DataFrame()

class ScreenerUI:
    def __init__(self):
        # Determine project root
        self.current_dir = Path(__file__).parent
        # src/jojo_trading/ui -> src/jojo_trading -> src -> root
        self.project_root = self.current_dir.parent.parent.parent
        
    def load_stock_list(self):
        json_path = self.project_root / "all_companies_basic_data.json"
        
        # Try finding it relative to CWD if project_root fails
        if not json_path.exists():
             json_path = Path("D:/Workspace/03.Dev_Projects/trading/jojo_trading/all_companies_basic_data.json")

        if json_path.exists():
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return pd.DataFrame(data)
            except Exception as e:
                st.error(f"無法載入股票列表: {e}")
                return pd.DataFrame()
        return pd.DataFrame()

    def render(self):
        st.subheader("🔍 股票形態篩選器")
        st.markdown("---")

        df_stocks = self.load_stock_list()

        if df_stocks.empty:
            st.warning("找不到股票列表資料 (all_companies_basic_data.json)")
            return

        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.info("設定篩選條件")
            # 選擇範圍
            industries = df_stocks['產業別'].unique().tolist()
            if "產業別" in df_stocks.columns:
                industries = sorted([x for x in industries if x])
            selected_industry = st.selectbox("選擇產業", ["全部"] + industries)

            if selected_industry != "全部":
                target_stocks = df_stocks[df_stocks['產業別'] == selected_industry]
            else:
                target_stocks = df_stocks

            total_stocks = len(target_stocks)
            st.caption(f"符合條件標的共: {total_stocks} 檔")

            # 限制數量
            limit_val = st.number_input(
                "篩選數量限制 (0 為全部掃描)", 
                min_value=0, 
                max_value=total_stocks, 
                value=50, 
                step=50,
                help="設為 0 代表掃描所有符合條件的股票。注意：掃描全部可能需要很長時間 (每 100 檔約需 1-2 分鐘)"
            )
            
            # 如果輸入 0，則 limit 為全部
            limit = total_stocks if limit_val == 0 else limit_val

            # 選擇形態
            st.markdown("##### 選擇形態")
            check_gc = st.checkbox("MA5/MA20 黃金交叉", value=True)
            check_dc = st.checkbox("MA5/MA20 死亡交叉")
            check_ma_break_up = st.checkbox("一陽穿三線 (強勢突破)", help="收盤價一舉突破 5/10/20 日均線")
            check_ma_break_down = st.checkbox("一陰穿三線 (深跌破線)", help="收盤價一舉跌破 5/10/20 日均線 (俗稱三生無奈)")
            check_four_seas = st.checkbox("四海游龍 (多頭排列)", help="5 > 10 > 20 > 60 MA，長期強勢格局")
            check_four_sides = st.checkbox("四面楚歌 (空頭排列)", help="5 < 10 < 20 < 60 MA，長期弱勢格局")
            check_rsi_over = st.checkbox("RSI 超買 (>70)")
            check_rsi_under = st.checkbox("RSI 超賣 (<30)")
            check_w_bottom = st.checkbox("W 底 (雙底) 形態")

            start_btn = st.button("🚀 開始執行篩選", type="primary", use_container_width=True)

        with col2:
            if start_btn:
                results = []
                # 取出代號列表
                stock_codes = target_stocks['公司代號'].tolist()[:limit]
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                total = len(stock_codes)
                
                # Placeholder for results
                result_container = st.container()
                
                for i, code in enumerate(stock_codes):
                    stock_name = target_stocks[target_stocks['公司代號'] == code]['公司名稱'].values[0]
                    status_text.text(f"正在分析: {code} {stock_name} ({i+1}/{total})")
                    progress_bar.progress((i + 1) / total)
                    
                    try:
                        # 下載數據 (使用快取)
                        ticker = f"{code}.TW"
                        
                        # 改用快取函式
                        df = fetch_stock_history_cached(ticker)
                        
                        if df.empty or len(df) < 30:
                            continue
                            
                        # Handle MultiIndex
                        if isinstance(df.columns, pd.MultiIndex):
                             # Try to flatten if needed, or just extract 'Close'
                             # yfinance v0.2 returns (Price, Ticker) as columns
                            try:
                                df = df.xs(ticker, axis=1, level=1)
                            except:
                                # Fallback if structure is different
                                df.columns = df.columns.get_level_values(0)

                        # Calculate
                        df = PatternRecognizer.calculate_indicators(df)
                        
                        matched_patterns = []
                        
                        if check_gc and PatternRecognizer.check_golden_cross(df):
                            matched_patterns.append("MA黃金交叉")
                        if check_dc and PatternRecognizer.check_death_cross(df):
                            matched_patterns.append("MA死亡交叉")
                        if check_ma_break_up and PatternRecognizer.check_ma_breakthrough_bullish(df):
                            matched_patterns.append("一陽穿三線")
                        if check_ma_break_down and PatternRecognizer.check_ma_breakthrough_bearish(df):
                            matched_patterns.append("一陰穿三線")
                        if check_four_seas and PatternRecognizer.check_bullish_perfect_order(df):
                            matched_patterns.append("四海游龍")
                        if check_four_sides and PatternRecognizer.check_bearish_perfect_order(df):
                            matched_patterns.append("四面楚歌")
                        if check_rsi_over and PatternRecognizer.check_rsi_overbought(df):
                            matched_patterns.append("RSI超買")
                        if check_rsi_under and PatternRecognizer.check_rsi_oversold(df):
                            matched_patterns.append("RSI超賣")
                        if check_w_bottom and PatternRecognizer.check_double_bottom(df):
                            matched_patterns.append("W底形態")
                            
                        if matched_patterns:
                            latest_close = float(df['Close'].iloc[-1])
                            latest_rsi = float(df['RSI'].iloc[-1]) if 'RSI' in df.columns else 0.0
                            
                            results.append({
                                "代號": code,
                                "名稱": stock_name,
                                "現價": round(latest_close, 2),
                                "RSI": round(latest_rsi, 2),
                                "符合形態": ", ".join(matched_patterns)
                            })
                            
                    except Exception as e:
                        print(f"Screener Error {code}: {e}")
                        pass
                        
                progress_bar.empty()
                status_text.empty()
                
                with result_container:
                    if results:
                        st.success(f"在此批次中找到 {len(results)} 檔符合條件的股票")
                        st.dataframe(pd.DataFrame(results), use_container_width=True)
                    else:
                        st.info("在此批次中沒有找到符合條件的股票。")
            else:
                st.markdown("""
                ### 👈 請在左側設定條件並執行
                
                此工具將協助您掃描選擇的股票範圍，找出符合特定技術形態的標的。
                
                **目前支援的形態：**
                - **MA 黃金交叉**: 短期趨勢轉強
                - **MA 死亡交叉**: 短期趨勢轉弱
                - **RSI 超買/超賣**: 尋找反轉與過熱訊號
                - **W 底 (雙底)**: 潛在的底部反轉形態
                
                *注意：即時掃描需要大量網路請求，請耐心等候。*
                """)
