import streamlit as st
import pandas as pd
import yfinance as yf
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

# 添加項目路徑
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from jojo_trading.analysis.patterns import PatternRecognizer

# 頁面標題
st.title("🔍 股票形態篩選器 (Stock Screener)")
st.markdown("---")

# 1. 載入股票列表
@st.cache_data
def load_stock_list():
    json_path = project_root / "all_companies_basic_data.json"
    if json_path.exists():
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return pd.DataFrame(data)
        except Exception as e:
            st.error(f"無法載入股票列表: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

df_stocks = load_stock_list()

if df_stocks.empty:
    st.warning("找不到股票列表資料 (all_companies_basic_data.json)")
    st.stop()

# 2. 側邊欄設定
st.sidebar.header("篩選設定")

# 選擇範圍
industries = df_stocks['產業別'].unique().tolist()
selected_industry = st.sidebar.selectbox("選擇產業", ["全部"] + industries)

if selected_industry != "全部":
    target_stocks = df_stocks[df_stocks['產業別'] == selected_industry]
else:
    target_stocks = df_stocks

# 限制數量 (避免太慢)
limit = st.sidebar.slider("篩選數量限制 (從前幾檔開始)", 10, 200, 50, help="為了避免等待過久，建議先用少量股票測試")

# 選擇形態
st.sidebar.subheader("選擇形態條件")
check_gc = st.sidebar.checkbox("MA5/MA20 黃金交叉", value=True)
check_dc = st.sidebar.checkbox("MA5/MA20 死亡交叉")
check_rsi_over = st.sidebar.checkbox("RSI 超買 (>70)")
check_rsi_under = st.sidebar.checkbox("RSI 超賣 (<30)")
check_w_bottom = st.sidebar.checkbox("W 底 (雙底) 形態")

# 3. 執行篩選
if st.button("🚀 開始篩選", type="primary"):
    
    results = []
    
    # 取出代號列表
    stock_codes = target_stocks['公司代號'].tolist()[:limit]
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total = len(stock_codes)
    
    for i, code in enumerate(stock_codes):
        stock_name = target_stocks[target_stocks['公司代號'] == code]['公司名稱'].values[0]
        status_text.text(f"正在分析: {code} {stock_name} ({i+1}/{total})")
        progress_bar.progress((i + 1) / total)
        
        try:
            # 下載數據 (使用 yfinance)
            # 台股代號需加 .TW
            ticker = f"{code}.TW"
            df = yf.download(ticker, period="6mo", interval="1d", progress=False)
            
            if df.empty or len(df) < 30:
                continue
                
            # 處理 MultiIndex columns (yfinance 0.2+ 可能會出現)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
                
            # 計算指標
            df = PatternRecognizer.calculate_indicators(df)
            
            matched_patterns = []
            
            # 檢查條件
            if check_gc and PatternRecognizer.check_golden_cross(df):
                matched_patterns.append("MA黃金交叉")
                
            if check_dc and PatternRecognizer.check_death_cross(df):
                matched_patterns.append("MA死亡交叉")
                
            if check_rsi_over and PatternRecognizer.check_rsi_overbought(df):
                matched_patterns.append("RSI超買")
                
            if check_rsi_under and PatternRecognizer.check_rsi_oversold(df):
                matched_patterns.append("RSI超賣")
                
            if check_w_bottom and PatternRecognizer.check_double_bottom(df):
                matched_patterns.append("W底形態")
                
            if matched_patterns:
                latest_close = df['Close'].iloc[-1]
                latest_rsi = df['RSI'].iloc[-1] if 'RSI' in df.columns else np.nan
                
                results.append({
                    "代號": code,
                    "名稱": stock_name,
                    "現價": round(latest_close, 2),
                    "RSI": round(latest_rsi, 2),
                    "符合形態": ", ".join(matched_patterns)
                })
                
        except Exception as e:
            # print(f"Error processing {code}: {e}")
            pass
            
    progress_bar.empty()
    status_text.empty()
    
    if results:
        st.success(f"篩選完成！找到 {len(results)} 檔符合條件的股票")
        st.dataframe(pd.DataFrame(results), use_container_width=True)
    else:
        st.info("沒有找到符合條件的股票。")

else:
    st.info("請從左側選擇條件並點擊「開始篩選」")
    
    # 顯示目前選擇的範圍預覽
    st.write(f"目前選擇範圍: {selected_industry} (共 {len(target_stocks)} 檔，將分析前 {limit} 檔)")
    st.dataframe(target_stocks[['公司代號', '公司名稱', '產業別']].head(limit))
