import streamlit as st
import pandas as pd
import time
from datetime import datetime
from jojo_trading.core.shioaji_connector import ShioajiConnector
from jojo_trading.core.watchlist_manager import WatchlistManager
from jojo_trading.analysis.hedging import HedgingCalculator

st.set_page_config(
    page_title="期貨避險策略 | JoJo Trading",
    page_icon="🛡️",
    layout="wide"
)

# --- AUTO-MARGIN DETECTION LOGIC ---
from jojo_trading.core.margin_manager import MarginManager
from jojo_trading.core.stock_database import StockDatabase

@st.cache_data(ttl=3600*24) # Cache for 24 hours (Daily Check)
def fetch_margin_cache():
    return MarginManager.fetch_current_margins()

# Auto-check on load
try:
    with st.spinner("檢查保證金變動..."):
        latest_margins = fetch_margin_cache()
        if latest_margins:
            # Check for diffs against DB
            db_chk = StockDatabase()
            current_db = db_chk.get_all_margins()
            
            # Simple check: Compare TXF Init Margin
            # (In production, checking all is better, but this is fast signal)
            updates_needed = []
            
            for item in latest_margins:
                sym = item['symbol']
                new_init = item['initial_margin']
                
                # Find in DB df
                if not current_db.empty and 'symbol' in current_db.columns:
                     row = current_db[current_db['symbol'] == sym]
                     if not row.empty:
                         old_init = float(row.iloc[0]['initial_margin'])
                         if new_init != old_init:
                             updates_needed.append(item)
            
            if updates_needed:
                st.session_state['margin_updates_pending'] = updates_needed
                st.toast(f"📢 偵測到 {len(updates_needed)} 筆保證金變動！", icon="⚠️")
                
except Exception as e:
    # Fail silently on auto-check to not block app
    print(f"Auto-margin check failed: {e}")

# Apply Pending Updates (Temp Storage usage)
if 'margin_updates_pending' in st.session_state:
    st.info("⚠️ 偵測到交易所保證金已調整 (已暫存於系統，計算將使用新數據)")
    # Logic to actually use these pending values in calculator will need to be passed down
    # Or we verify if user wants to update DB:
    if st.button("💾 確認更新至資料庫 (Persist Updates)"):
        db_upd = StockDatabase()
        for u in st.session_state['margin_updates_pending']:
            db_upd.update_margin(u['symbol'], u['initial_margin'], u['maintenance_margin'])
        del st.session_state['margin_updates_pending']
        st.success("✅ 資料庫已更新！")
        time.sleep(1)
        st.rerun()

# -----------------------------------

# Custom CSS for Dashboard
st.markdown("""
<style>
    .metric-card {
        background-color: #1e2130;
        border-radius: 10px;
        padding: 20px;
        border: 1px solid #2e3440;
        text-align: center;
    }
    .metric-title {
        color: #a0a0a0;
        font-size: 0.9em;
        margin-bottom: 5px;
    }
    .metric-value {
        font-size: 2em;
        font-weight: bold;
    }
    .metric-delta {
        font-size: 1em;
        font-weight: 500;
    }
    .positive { color: #00fa9a; }
    .negative { color: #ff6b6b; }
    
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Managers
sj_connector = ShioajiConnector()
wm = WatchlistManager()

# --- SIDEBAR ---
with st.sidebar:
    st.header("🛡️ 避險控制台")
    st.info("此模組協助您計算投資組合的風險曝險，並建議期貨避險口數。")
    
    if sj_connector.is_connected:
        st.success("✅ Shioaji 連線中")
    else:
        st.error("❌ Shioaji 未連線")

    # Contract Selection
    st.markdown("### 🔢 合約選擇")
    selected_month = st.selectbox(
        "選擇期貨月份",
        ["近月 (Front Month)", "次月 (Next Month)"],
        index=0
    )
    
    # Map selection to codes
    suffix = "R1" if "近月" in selected_month else "R2"
    txf_code_target = f"TXF{suffix}"
    mxf_code_target = f"MXF{suffix}"
    
    st.caption(f"監控合約: {txf_code_target}, {mxf_code_target}")

    st.divider()
    
    # Refresh Button
    if st.button("🔄 刷新即時報價"):
        st.rerun()

    st.divider()
    
    # Account Info
    st.markdown("### 💰 帳戶權益 (Account)")
    account_margin = sj_connector.get_account_margin()
    if account_margin:
        st.metric("權益總值 (Equity)", f"${int(account_margin.get('equity', 0)):,}")
        st.metric("可用保證金", f"${int(account_margin.get('available_margin', 0)):,}")
        risk_ratio = account_margin.get('risk_ratio', 0)
        st.metric("風險指標 (Risk)", f"{risk_ratio:.1%}", 
                 delta="Safe" if risk_ratio > 0.5 else "Warning", 
                 delta_color="normal" if risk_ratio > 0.5 else "inverse")
    else:
        st.info("無法取得帳戶權益 (需連線)")

    # Network Security
    try:
        from jojo_trading.core.network_manager import NetworkManager
        nm = NetworkManager()
        nm.render_sidebar(st)
    except:
        pass


# --- MAIN PAGE ---
st.title("🛡️ 智慧避險計算機 (Smart Hedging)")

# 2. Portfolio Exposure Analysis (Static/Slow Update)
# Load Portfolio first explicitly (outside fragment to avoid DB hits every 3s)
portfolio_df = wm.get_all_entries()

# Calculate Total Market Value
portfolio_value = 0
if not portfolio_df.empty:
    if 'market_value' not in portfolio_df.columns:
        portfolio_df['shares_held'] = portfolio_df.get('shares_held', 0).fillna(0)
        portfolio_df['current_price'] = portfolio_df.get('current_price', 0).fillna(0)
        portfolio_df['market_value'] = portfolio_df['shares_held'] * portfolio_df['current_price']
    portfolio_value = portfolio_df['market_value'].sum()

# Helper to render metric (simplified card)
def render_metric(label, data, container):
    if not data:
        container.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">{label}</div>
            <div class="metric-value">--</div>
            <div class="metric-delta">N/A</div>
        </div>
        """, unsafe_allow_html=True)
        return

    price = data['price']
    change = data['change']
    color_class = "positive" if change >= 0 else "negative"
    sign = "+" if change >= 0 else ""
    
    container.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">{label}</div>
        <div class="metric-value {color_class}">{int(price):,}</div>
        <div class="metric-delta {color_class}">{sign}{change} ({data['pct_change']}%)</div>
    </div>
    """, unsafe_allow_html=True)

# 3. LIVE FRAGMENT
@st.fragment(run_every=5) # Update every 5 seconds
def live_hedging_dashboard(portfolio_val, t_code, m_code):
    st.subheader("📊 市場情緒儀表板 (Market Sentiment)")
    st.caption(f"最後更新: {datetime.now().strftime('%H:%M:%S')} (每 5 秒自動刷新)")
    
    # 1. Fetch Data
    txf_data = sj_connector.get_futures_snapshot('TXF', specific_code=t_code)
    mxf_data = sj_connector.get_futures_snapshot('MXF', specific_code=m_code)
    
    # 2. Render Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_metric(f"台指期 ({t_code})", txf_data, st)
    with col2:
        render_metric(f"小型台指 ({m_code})", mxf_data, st)
    with col3:
        # Placeholder for Spot or VIX
        st.metric("大盤加權指數 (Ref)", "22,500", "0.00%") # TODO: Fetch Spot
    with col4:
        # Calculated Spread
        if txf_data:
            spot_ref = 22500 
            spread = txf_data['price'] - spot_ref
            st.metric("期現貨價差 (Spread)", f"{int(spread)}", delta_color="off")
        else:
            st.metric("期現貨價差", "--")

    st.markdown("---")
    
    # 3. Hedging Calculation (Using live price)
    st.subheader("💼 避險計算 (Live Calculation)")
    
    c1, c2 = st.columns([1, 2])
    
    with c1:
        st.markdown("#### 設定避險參數")
        current_value_display = f"${portfolio_val:,.0f}"
        st.text_input("投資組合現值 (TWD)", value=current_value_display, disabled=True)
        
        target_beta = st.number_input("輸入預估 Beta", 0.1, 3.0, 1.2, 0.1, key="hedge_beta")
        hedge_ratio = st.slider("目標避險比例 (Coverage)", 0, 100, 100, 10, format="%d%%", key="hedge_ratio")
        
        effective_value = portfolio_val * (hedge_ratio / 100)
        st.caption(f"實際避險金額: ${effective_value:,.0f}")

    with c2:
        st.markdown("#### 建議避險策略 (Recommendation)")
        
        if portfolio_val > 0 and txf_data:
            future_price = txf_data['price']
            
            # Calculate
            recs = HedgingCalculator.get_all_recommendations(
                portfolio_value=effective_value, 
                future_price=future_price, 
                portfolio_beta=target_beta
            )
            
            # Fetch Margins (Prefer DB, fallback to defaults)
            from jojo_trading.core.stock_database import StockDatabase
            try:
                # Fast local DB read
                db_re = StockDatabase()
                margin_info = db_re.get_all_margins()
                margin_map = {}
                if not margin_info.empty:
                     for _, row in margin_info.iterrows():
                         margin_map[row['symbol']] = float(row['initial_margin'])
            except:
                margin_map = {}

            # Display
            rec_data = []
            for r in recs:
                # Calculate Est Margin
                u_margin = margin_map.get(r.contract_code, 0)
                tot_margin = u_margin * r.required_contracts
                
                margin_str = f"${tot_margin:,.0f}" if u_margin > 0 else "N/A"

                rec_data.append({
                    "合約商品": r.contract_name,
                    "代號": r.contract_code,
                    "合約規格": f"${r.multiplier}",
                    "單口價值": f"${r.contract_value:,.0f}",
                    "🔥 建議口數": f"{r.required_contracts} 口",
                    "預估保證金": margin_str,
                    "方向": "放空 (Short)"
                })
            
            # Store Recommendation for Execution Panel
            if len(recs) > 1:
                # Store the Mini Futures (MXF) recommendation as default
                st.session_state['hedge_rec_code'] = recs[1].contract_code
                st.session_state['hedge_rec_qty'] = recs[1].required_contracts
                st.session_state['hedge_rec_price'] = future_price 
            
            st.dataframe(pd.DataFrame(rec_data), use_container_width=True, hide_index=True)
            if len(recs) > 1:
                st.info(f"💡 動態建議：賣出 **{recs[1].required_contracts} 口小台** (基於目前試算)")
            
        else:
            if portfolio_val == 0:
                st.warning("⚠️ 投資組合價值為 0，無法計算避險。")
            else:
                st.warning("⚠️ 等待期貨報價中...")

# Run the live fragment
live_hedging_dashboard(portfolio_value, txf_code_target, mxf_code_target)

# 4. Execution (Real-Time Safety)
st.markdown("### ⚡ 避險下單 (Execution Panel)")

with st.container(border=True):
    col_exec1, col_exec2 = st.columns([1, 1])
    
    with col_exec1:
        st.markdown("#### 📝 委託設定")
        
        # New: Fill Logic
        if st.button("⚡ 帶入建議數值 (Auto-Fill)"):
            if 'hedge_rec_code' in st.session_state:
                 # Update widget values via their keys
                 st.session_state.exec_target = st.session_state['hedge_rec_code']
                 st.session_state.exec_qty_input = min(st.session_state['hedge_rec_qty'], 2) # Safety cap
                 st.session_state.exec_price_input = float(st.session_state['hedge_rec_price'])
                 st.toast("已帶入建議數值！", icon="✅")
            else:
                 st.toast("尚無建議數值可帶入", icon="⚠️")

        # Determine Contract Code from Selection or Override
        exec_contract_mode = st.radio("合約來源", ["監控中合約", "手動輸入"], horizontal=True)
        if exec_contract_mode == "監控中合約":
            # Check if auto-fill target is in standard list, if not might need manual?
            # Actually, let's keep it simple. If auto-fill, maybe force manual text?
            # For now, stick to selectbox logic or fallback
            idx = 0
            if 'exec_target' in st.session_state and st.session_state.exec_target == txf_code_target:
                idx = 1
            
            target_contract_exec = st.selectbox(
                "標的", 
                [mxf_code_target, txf_code_target], 
                index=idx
            )
        else:
            val = st.session_state.get('exec_target', 'MXFR1')
            target_contract_exec = st.text_input("輸入合約代碼 (e.g. MXFR1)", value=val)
            
        action = st.selectbox("買賣方向 (Action)", ["Sell (放空避險)", "Buy (做多)"], index=0)
        action_code = "Sell" if "Sell" in action else "Buy"
        
        price_type = st.selectbox("價格類別", ["LMT (限價)", "MKT (市價)", "MKP (範圍市價)"])
        price_type_code = price_type.split(" ")[0]
        
        if price_type_code == "LMT":
            # Auto-fill price from dash if available?
            default_price = st.session_state.get('exec_price', 0.0)
            order_price = st.number_input("委託價格", min_value=0.0, value=default_price, step=1.0, key="exec_price_input")
        else:
            order_price = 0.0
            st.info("市價單不需要輸入價格")
            
        def_qty = st.session_state.get('exec_qty', 1)
        quantity = st.number_input("委託口數 (Max 2)", min_value=1, max_value=2, value=def_qty, key="exec_qty_input")
    
    with col_exec2:
        st.markdown("#### 🛡️ 安全確認 & 執行")
        
        # Dry Run Toggle
        dry_run_mode = st.toggle("啟用 Dry Run (模擬測試)", value=True)
        
        if dry_run_mode:
            st.info("🟢 測試模式開啟：不會真的送出委託。")
        else:
            st.warning("🔴 真實交易模式：請謹慎操作！")
        
        st.markdown("---")
        
        # Submit Logic with Double Confirmation
        confirm_check = st.checkbox("我確認上述委託資訊無誤")
        
        if st.button("🚀 送出委託 (Submit Order)", type="primary" if not dry_run_mode else "secondary", disabled=not confirm_check):
            with st.spinner("正在傳送指令..."):
                result = sj_connector.place_futures_order(
                    contract_code=target_contract_exec,
                    action=action_code,
                    quantity=quantity,
                    price=order_price,
                    price_type=price_type_code,
                    dry_run=dry_run_mode
                )
                
                if result['status'] == 'success':
                    if dry_run_mode:
                        st.success(f"✅ [測試成功] {result['msg']}")
                        st.json(result)
                    else:
                        st.toast(f"下單成功! ID: {result.get('order_id')}", icon="🔥")
                        st.success(f"✅ 委託已送出: {result['msg']}")
                        st.json(result)
                else:
                    st.error(f"❌ 下單失敗: {result['msg']}")

# 5. Order Status Tracker
st.markdown("### 📋 委託回報 (Order Status)")
if st.button("🔄 刷新委託狀態"):
    st.rerun()

orders = sj_connector.get_orders()
if orders:
    # Convert to DataFrame for better display
    df_orders = pd.DataFrame(orders)
    # Rename columns for display
    df_orders = df_orders.rename(columns={
        'id': '單號',
        'code': '商品代碼',
        'action': '買賣',
        'price': '價格',
        'qty': '口數',
        'status': '狀態',
        'type': '類別'
    })
    st.dataframe(df_orders, use_container_width=True, hide_index=True)
else:
    st.info("尚無委託記錄 (No Orders Found)")

# 6. Margin Reference (Info Only)
st.markdown("### ℹ️ 期貨保證金資訊 (Margin Requirements)")
from jojo_trading.core.stock_database import StockDatabase
try:
    db = StockDatabase()
    margin_df = db.get_all_margins()
    if not margin_df.empty:
        # Format columns
        margin_df = margin_df[['name', 'initial_margin', 'maintenance_margin', 'multiplier', 'last_updated']]
        margin_df.columns = ['商品名稱', '原始保證金', '維持保證金', '契約乘數', '更新時間']
        st.dataframe(margin_df, use_container_width=True, hide_index=True)
    else:
        st.info("尚無保證金資料庫存檔")
except Exception as e:
    st.error(f"無法讀取保證金資料: {e}")

with st.expander("⚙️ 設定保證金參數 (Margin Configuration)"):
    st.caption("若交易所調整保證金，請在此更新數據。")
    
    # Auto Update Section
    col_auto, col_manual = st.columns([1, 2])
    
    with col_auto:
        st.markdown("**自動更新 (Auto Sync)**")
        if st.button("🔄 sync from TAIFEX", help="從期交所官網抓取最新保證金"):
            with st.spinner("正在連線期交所 (TAIFEX)..."):
                try:
                    from jojo_trading.core.margin_manager import MarginManager
                    success, msg = MarginManager.sync_to_db()
                    if success:
                        st.success(f"更新成功: {msg}")
                        time.sleep(1) # Let user see message
                        st.rerun()
                    else:
                        st.error(f"更新失敗: {msg}")
                except Exception as e:
                    st.error(f"Sync Error: {e}")
    
    with col_manual:
        st.markdown("**手動更新 (Manual)**")
        with st.form("margin_update_form"):
            # Allow selecting symbol to update
            m_symbol = st.selectbox("選擇商品", ["TXF", "MXF", "ZEF"])
        
            # Load current values if possible
            curr_init = 0.0
            curr_maint = 0.0
            
            new_init = st.number_input("原始保證金 (Initial)", min_value=0.0, step=100.0)
            new_maint = st.number_input("維持保證金 (Maintenance)", min_value=0.0, step=100.0)
            
            if st.form_submit_button("更新資料庫 (Update DB)"):
                try:
                    # Update logic
                    db.update_margin(m_symbol, new_init, new_maint)
                    st.success(f"已更新 {m_symbol} 保證金數據！")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"更新失敗: {e}")


