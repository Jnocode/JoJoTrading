"""
DCF估值分析頁面
統一的DCF估值分析介面 - 個股分析和類股篩選
使用自動資料抓取，提供真實財務數據驅動的DCF計算
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# 添加項目路徑
current_dir = Path(__file__).parent
project_root = current_dir.parent
src_path = project_root / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

# 嘗試導入自動資料抓取器
try:
    from jojo_trading.core.auto_data_fetcher import AutoDataFetcher
    AUTO_DATA_FETCHER_AVAILABLE = True
    print("✅ AutoDataFetcher 導入成功")
except ImportError as e:
    AUTO_DATA_FETCHER_AVAILABLE = False
    print(f"❌ AutoDataFetcher 導入失敗: {e}")

# 嘗試導入類股篩選組件
try:
    from jojo_trading.ui.components.sector_screening import SectorScreeningComponent
    SECTOR_SCREENING_AVAILABLE = True
except ImportError:
    SECTOR_SCREENING_AVAILABLE = False

# 嘗試導入行業特定參數
try:
    from jojo_trading.core.industry_dcf_params import (
        get_industry_params, 
        get_adjusted_screening_params, 
        get_stock_specific_params,
        INDUSTRY_DCF_PARAMS
    )
    INDUSTRY_PARAMS_AVAILABLE = True
    print("✅ 行業特定DCF參數模組載入成功")
except ImportError as e:
    INDUSTRY_PARAMS_AVAILABLE = False
    print(f"❌ 行業特定DCF參數模組載入失敗: {e}")

# 嘗試導入資料替代方案管理器
try:
    from jojo_trading.core.data_fallback_manager import DataFallbackManager
    DATA_FALLBACK_AVAILABLE = True
    print("✅ 資料替代方案管理器載入成功")
except ImportError as e:
    DATA_FALLBACK_AVAILABLE = False
    print(f"❌ 資料替代方案管理器載入失敗: {e}")

# 嘗試導入股票資料庫
try:
    from jojo_trading.core.stock_database import StockDatabase
    STOCK_DB_AVAILABLE = True
    print("✅ 股票資料庫載入成功")
except ImportError as e:
    STOCK_DB_AVAILABLE = False
    print(f"❌ 股票資料庫載入失敗: {e}")

# ⚠️ 注意：在多頁面應用中，頁面檔案不應該調用 st.set_page_config()
# 頁面配置應該在主應用檔案（app.py 或 Home.py）中設定

# 初始化自動資料抓取器
@st.cache_resource
def init_auto_data_fetcher():
    """初始化並快取自動資料抓取器"""
    if AUTO_DATA_FETCHER_AVAILABLE:
        try:
            fetcher = AutoDataFetcher()
            return fetcher
        except Exception as e:
            st.error(f"AutoDataFetcher 初始化失敗: {e}")
            return None
    return None

auto_fetcher = init_auto_data_fetcher()

def map_sector_code_to_name(code_or_name):
    """將行業代碼或名稱映射到 UI 顯示的類別"""
    if not code_or_name:
        return "其他"
    
    # 移除空白並轉字串
    key = str(code_or_name).strip()
        
    # 代碼映射 (參考 industries.json)
    code_mapping = {
        "24": "半導體",
        "17": "金融",
        "03": "塑膠",
        "10": "鋼鐵",
        "12": "汽車",
        "27": "電信",
        "28": "電子", # 電子零組件
        "25": "電子", # 電腦及週邊
        "26": "電子", # 光電
        "13": "電子", # 電子工業
        "29": "電子", # 電子通路
        "30": "電子", # 資訊服務
        "31": "電子", # 其他電子
        "01": "水泥",
        "02": "食品",
        "11": "橡膠",
        "14": "建材營造",
        "15": "航運",
        "16": "觀光",
        "22": "生技",
        "23": "油電燃氣",
    }
    
    # 如果是代碼，直接映射
    if key in code_mapping:
        return code_mapping[key]
        
    # 名稱關鍵字映射 (如果傳入的是名稱)
    if "半導體" in key: return "半導體"
    if "金融" in key or "銀行" in key or "保險" in key or "金控" in key: return "金融"
    if "電子" in key or "電腦" in key or "光電" in key: return "電子"
    if "電信" in key or "通信" in key: return "電信"
    if "塑膠" in key: return "塑膠"
    if "鋼鐵" in key: return "鋼鐵"
    if "汽車" in key: return "汽車"
    if "水泥" in key: return "水泥"
    if "食品" in key: return "食品"
    if "航運" in key: return "航運"
    if "生技" in key or "生醫" in key: return "生技"
    if "觀光" in key or "飯店" in key: return "觀光"
    if "營造" in key or "建設" in key: return "建材營造"
    
    return "其他"

def get_stock_data_from_auto_fetcher(stock_code):
    """使用自動資料抓取器獲取股票財務數據 - 增強版含多資料源切換"""
    if not auto_fetcher:
        # 降級使用虛擬資料
        return get_stock_data_fallback(stock_code)
    
    try:
        # 首先嘗試標準的資料抓取
        dcf_data = auto_fetcher.get_dcf_ready_data(stock_code)
        
        # 如果標準抓取失敗，使用增強版多資料源抓取
        if not dcf_data.get('success', False):
            st.warning(f"⚠️ 標準資料抓取失敗，嘗試多資料源切換...")
            
            if DATA_FALLBACK_AVAILABLE:
                fallback_manager = DataFallbackManager(auto_fetcher)
                dcf_data = fallback_manager.get_enhanced_data_with_fallback(stock_code)
                
                if dcf_data and dcf_data.get('success'):
                    st.info(f"✅ 成功從 {dcf_data.get('data_source', '替代資料源')} 獲取資料")
                else:
                    st.error(f"❌ 所有資料源都失敗，使用備用資料")
                    return get_stock_data_fallback(stock_code)
            else:
                return get_stock_data_fallback(stock_code)
        
        # 使用增強版資料處理（包含替代方案）
        if DATA_FALLBACK_AVAILABLE:
            fallback_manager = DataFallbackManager(auto_fetcher)
            enhanced_fcf_data = fallback_manager.calculate_enhanced_free_cash_flow(stock_code, dcf_data)
            
            # 顯示資料品質資訊
            data_quality = enhanced_fcf_data['data_quality']
            estimates_used = enhanced_fcf_data['estimates_used']
            data_source = dcf_data.get('data_source', '自動抓取')
            
            if estimates_used:
                st.info(f"📊 資料品質: {data_quality} | 資料源: {data_source} | 使用估算: {', '.join(estimates_used)}")
            else:
                st.success(f"📊 資料品質: {data_quality} | 資料源: {data_source} | 完整真實資料")
            
            free_cash_flow = enhanced_fcf_data['free_cash_flow']
            net_income = enhanced_fcf_data['net_income']
            capex = enhanced_fcf_data['capex']
            depreciation = enhanced_fcf_data['depreciation']
        else:
            # 原始計算方式（當替代方案不可用時）
            net_income = dcf_data.get('net_income_parent', 0) / 1e8  # 轉換為億元
            depreciation = dcf_data.get('depreciation', 0) / 1e8
            amortization = dcf_data.get('amortization', 0) / 1e8
            capex = dcf_data.get('capex', 0) / 1e8
            
            # 簡化版營運資金變化計算 (可進一步優化)
            working_capital_change = 0  # 暫時簡化
            
            free_cash_flow = net_income + depreciation + amortization - capex - working_capital_change
            
            # 資料缺失警告
            missing_fields = []
            if not dcf_data.get('capex'):
                missing_fields.append('資本支出')
            if not dcf_data.get('depreciation'):
                missing_fields.append('折舊費用')
            
            if missing_fields:
                st.warning(f"⚠️ 缺少關鍵欄位: {', '.join(missing_fields)}，可能影響計算準確性")
        
        # 轉換為 DCF 計算函數期望的格式
        # 獲取並映射行業分類
        raw_sector = dcf_data.get('sector', '')
        mapped_sector = map_sector_code_to_name(raw_sector)
        
        return {
            "company_name": dcf_data.get('company_name', f'股票 {stock_code}'),
            "free_cash_flow": max(free_cash_flow, 1.0),  # 確保非負值
            "current_price": dcf_data.get('current_market_price', 100),
            "shares_outstanding": dcf_data.get('shares_outstanding', 100000000) / 1e8,  # 轉換為億股
            "sector": mapped_sector,  # 使用映射後的行業分類
            "data_source": "auto_fetcher",
            "net_income": net_income,
            "capex": capex,
            "depreciation": depreciation
        }
        
    except Exception as e:
        st.error(f"❌ 自動抓取過程發生錯誤: {e}")
        return get_stock_data_fallback(stock_code)

def get_stock_data_fallback(stock_code):
    """降級方案：虛擬資料庫"""
    # 模擬數據庫，實際使用時可替換為真實API
    stock_database = {
        "2330": {"company_name": "台灣積體電路製造", "free_cash_flow": 800.5, "current_price": 580, "shares_outstanding": 259.3, "sector": "半導體"},
        "2317": {"company_name": "鴻海精密", "free_cash_flow": 150.2, "current_price": 105, "shares_outstanding": 139.0, "sector": "電子"},
        "2454": {"company_name": "聯發科技", "free_cash_flow": 45.8, "current_price": 920, "shares_outstanding": 15.9, "sector": "半導體"},
        "2412": {"company_name": "中華電信", "free_cash_flow": 120.3, "current_price": 120, "shares_outstanding": 77.5, "sector": "電信"},
        "2882": {"company_name": "國泰金控", "free_cash_flow": 280.1, "current_price": 55, "shares_outstanding": 106.7, "sector": "金融"},
        "2881": {"company_name": "富邦金控", "free_cash_flow": 245.6, "current_price": 68, "shares_outstanding": 127.8, "sector": "金融"},
        "2886": {"company_name": "兆豐金控", "free_cash_flow": 180.4, "current_price": 35, "shares_outstanding": 120.6, "sector": "金融"},
        "2303": {"company_name": "聯電", "free_cash_flow": 35.2, "current_price": 48, "shares_outstanding": 124.3, "sector": "半導體"},
        "2308": {"company_name": "台達電", "free_cash_flow": 42.1, "current_price": 340, "shares_outstanding": 26.0, "sector": "電子"},
        "1301": {"company_name": "台塑", "free_cash_flow": 58.9, "current_price": 95, "shares_outstanding": 37.8, "sector": "塑膠"},
        "2002": {"company_name": "中鋼", "free_cash_flow": 68.5, "current_price": 28, "shares_outstanding": 218.7, "sector": "鋼鐵"},
        "2207": {"company_name": "和泰車", "free_cash_flow": 28.3, "current_price": 620, "shares_outstanding": 6.8, "sector": "汽車"},
    }
    
    fallback_data = stock_database.get(stock_code, {
        "company_name": f"公司代碼 {stock_code}",
        "free_cash_flow": 50.0,
        "current_price": 100,
        "shares_outstanding": 100.0,
        "sector": "其他"
    })
    fallback_data["data_source"] = "fallback"
    return fallback_data

def get_stock_data(stock_code):
    """統一的股票資料獲取介面"""
    return get_stock_data_from_auto_fetcher(stock_code)

def calculate_dcf_with_potential_return(stock_data, growth_rate, terminal_growth, discount_rate, years=5):
    """統一的DCF估值計算函數 - 返回潛在報酬率"""
    current_fcf = stock_data["free_cash_flow"]
    current_price = stock_data["current_price"]
    shares_outstanding = stock_data["shares_outstanding"]
    
    if discount_rate <= terminal_growth:
        return None, "折現率必須大於永續成長率"
    
    # 計算未來現金流的現值
    present_values = []
    fcf_projections = []
    
    for year in range(1, years + 1):
        future_fcf = current_fcf * (1 + growth_rate/100)**year
        present_value = future_fcf / (1 + discount_rate/100)**year
        present_values.append(present_value)
        fcf_projections.append({
            '年度': f'第{year}年',
            '預測現金流': f'{future_fcf:.1f}億',
            '現值': f'{present_value:.1f}億',
            '成長率': f'{growth_rate:.1f}%'
        })
    
    # 計算終值
    terminal_fcf = current_fcf * (1 + growth_rate/100)**years
    terminal_value = terminal_fcf * (1 + terminal_growth/100) / ((discount_rate/100) - (terminal_growth/100))
    terminal_pv = terminal_value / (1 + discount_rate/100)**years
      # 企業總價值和每股內在價值
    total_pv = sum(present_values)
    enterprise_value = total_pv + terminal_pv
    intrinsic_value_per_share = enterprise_value / shares_outstanding  # 億元 / 億股 = 元/股
    
    # 計算潛在報酬率
    potential_return = ((intrinsic_value_per_share - current_price) / current_price) * 100
    
    # 計算當前市值
    current_market_value = current_price * shares_outstanding  # 元 * 億股 = 億元
    
    return {
        'enterprise_value': enterprise_value,
        'total_pv': total_pv,
        'terminal_pv': terminal_pv,
        'fcf_projections': fcf_projections,
        'current_fcf': current_fcf,
        'intrinsic_value_per_share': intrinsic_value_per_share,
        'current_price': current_price,
        'potential_return': potential_return,
        'current_market_value': current_market_value,
        'shares_outstanding': shares_outstanding,
        'company_name': stock_data["company_name"],
        'sector': stock_data["sector"]
    }, None

def calculate_sensitivity_analysis(stock_data, base_growth, base_terminal, base_discount):
    """
    計算敏感度分析矩陣
    X軸: 永續成長率 (Terminal Growth)
    Y軸: 折現率 (Discount Rate)
    值: 潛在報酬率
    """
    # 設定變動範圍
    discount_range = [base_discount - 1.0, base_discount - 0.5, base_discount, base_discount + 0.5, base_discount + 1.0]
    terminal_range = [base_terminal - 0.5, base_terminal - 0.25, base_terminal, base_terminal + 0.25, base_terminal + 0.5]
    
    results = []
    
    for d_rate in discount_range:
        row_data = {}
        # 格式化 Y 軸標籤
        row_label = f"折現率 {d_rate:.1f}%"
        row_data['index'] = row_label
        
        for t_rate in terminal_range:
            # 確保參數合理
            if d_rate <= t_rate:
                row_data[f"{t_rate:.2f}%"] = "N/A"
                continue
                
            # 簡化計算 (不需生成完整報告，只需潛在報酬)
            res, _ = calculate_dcf_with_potential_return(stock_data, base_growth, t_rate, d_rate)
            if res:
                row_data[f"{t_rate:.2f}%"] = res['potential_return']
            else:
                row_data[f"{t_rate:.2f}%"] = -999
        
        results.append(row_data)
    
    # 轉為 DataFrame
    df = pd.DataFrame(results)
    df.set_index('index', inplace=True)
    return df

def get_all_stocks_for_screening():
    """獲取所有股票用於類股篩選 - 使用自動資料抓取"""
    # 台股主要股票清單 (擴充版)
    major_stocks = [
        # 半導體
        "2330", "2454", "2303", "2379", "3711", "8110",
        # 金融
        "2882", "2881", "2886", "2891", "2884",
        # 電子/電腦/光電
        "2317", "2308", "2357", "2345", "2382", "2395", "2409", "3231", "2353",
        # 傳產 (塑膠/鋼鐵/水泥/食品/汽車)
        "1301", "6505", "2002", "1101", "1216", "2207",
        # 航運
        "2603", "2609", "2615",
        # 電信
        "2412", "3045", "4904",
        # 其他 (生技/觀光/營造)
        "6446", "2707", "2501"
    ]
    
    stocks_data = []
    for stock_code in major_stocks:
        try:
            stock_data = get_stock_data(stock_code)
            if stock_data:
                # 添加股票代碼到資料中
                stock_data['stock_code'] = stock_code
                stocks_data.append(stock_data)
        except Exception as e:
            st.warning(f"⚠️ 獲取 {stock_code} 資料時發生錯誤: {e}")
            continue
    
    return stocks_data

# 頁面標題
st.title("📊 DCF估值分析")
st.markdown("**專業的DCF估值分析工具 - 統一算法，準確估值**")

# 資料來源狀態顯示
if AUTO_DATA_FETCHER_AVAILABLE and auto_fetcher:
    st.success("🔄 **真實資料模式** - 使用 FinMind API 自動抓取即時財務數據")
else:
    st.warning("⚠️ **示範資料模式** - 使用虛擬資料，請檢查 AutoDataFetcher 模組")

# 主要功能標籤頁
tab1, tab2 = st.tabs(["📈 個股DCF分析", "🎯 類股篩選DCF"])

with tab1:
    st.markdown("### 🎯 找出個股的潛在報酬")
    st.info("💡 輸入股票代碼，立即獲得基於DCF估值的潛在報酬率")

    st.markdown("---")

    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 輸入參數")
        stock_code = st.text_input("股票代碼", placeholder="例如: 2330", help="請輸入台股股票代碼")
          # 根據輸入的股票代碼動態調整預設參數
        default_growth = 5.0
        default_terminal = 2.0
        default_discount = 8.0
        industry_info = None
        
        if stock_code and INDUSTRY_PARAMS_AVAILABLE:
            # 先獲取股票資料以判斷行業
            temp_stock_data = get_stock_data(stock_code)
            if temp_stock_data:
                sector = temp_stock_data.get('sector', '其他')
                
                # 嘗試獲取個股特定參數
                try:
                    stock_params = get_stock_specific_params(stock_code, sector)
                    default_growth = stock_params['growth_rate']
                    default_terminal = stock_params['terminal_growth']
                    default_discount = stock_params['discount_rate']
                    
                    # 顯示參數來源資訊
                    if stock_params['source'] == 'stock_specific':
                        st.success(f"🎯 **個股特定參數** - {temp_stock_data.get('company_name', stock_code)}")
                        st.info(f"📊 {stock_params['adjustment_reason']}")
                    else:
                        st.info(f"🏭 **行業參數**: {sector} | **風險等級**: {stock_params['volatility']}")
                        st.caption(f"💡 {stock_params['description']}")
                        
                except Exception as e:
                    # 降級使用行業參數
                    industry_params = get_industry_params(sector)
                    default_growth = industry_params['growth_rate']
                    default_terminal = industry_params['terminal_growth']
                    default_discount = industry_params['discount_rate']
                    
                    st.info(f"🏭 **行業**: {sector} | **風險等級**: {industry_params['volatility']}")
                    st.caption(f"💡 {industry_params['description']}")
        
        st.markdown("**調整估值參數** (已根據行業自動調整)")
        growth_rate = st.number_input("預期成長率 (%)", value=default_growth, step=0.1, 
                                      help="未來5年的預期年成長率", min_value=-10.0, max_value=50.0)
        terminal_growth = st.number_input("永續成長率 (%)", value=default_terminal, step=0.1, 
                                          help="穩定期的長期成長率", min_value=0.0, max_value=10.0)
        discount_rate = st.number_input("折現率 (%)", value=default_discount, step=0.1, 
                                        help="反映投資風險的貼現率", min_value=1.0, max_value=20.0)
        
        # 顯示參數調整說明
        if industry_info:
            with st.expander("📊 行業特定參數說明"):
                st.markdown(f"""
                **{temp_stock_data.get('sector', '未知')}行業特性**:
                - **建議成長率**: {industry_info['growth_rate']}%
                - **建議永續成長率**: {industry_info['terminal_growth']}%  
                - **建議折現率**: {industry_info['discount_rate']}%
                - **風險等級**: {industry_info['volatility']}
                
                💡 **說明**: {industry_info['description']}
                """)

    with col2:
        st.subheader("🎯 潛在報酬分析")
        
        if st.button("🚀 計算潛在報酬", type="primary", use_container_width=True):
            if stock_code:
                with st.spinner("📊 正在計算潛在報酬..."):
                    # 獲取股票數據並計算DCF
                    stock_data = get_stock_data(stock_code)
                    result, error = calculate_dcf_with_potential_return(stock_data, growth_rate, terminal_growth, discount_rate)
                    
                    if error:
                        st.error(f"❌ {error}")
                    elif result:                        # 顯示公司基本資訊
                        data_source_icon = "🔄" if stock_data.get('data_source') == 'auto_fetcher' else "🔧"
                        data_source_text = "真實資料" if stock_data.get('data_source') == 'auto_fetcher' else "示範資料"
                        st.success(f"✅ **{result['company_name']}** ({result['sector']}) {data_source_icon} {data_source_text}")
                        
                        # 資料來源詳細資訊
                        if stock_data.get('data_source') == 'auto_fetcher':
                            st.info("📡 **資料來源**: FinMind API 即時抓取")
                            if 'net_income' in stock_data:
                                st.caption(f"📊 基礎數據 - 淨利: {stock_data['net_income']:.1f}億 | 資本支出: {stock_data.get('capex', 0):.1f}億 | 折舊: {stock_data.get('depreciation', 0):.1f}億")
                        else:
                            st.warning("⚠️ **資料來源**: 示範用虛擬資料，實際投資請參考真實財報")
                        
                        # 🚀 潛在報酬率 - 核心指標
                        potential_return = result['potential_return']
                        
                        if potential_return > 20:
                            st.success(f"### 🚀 潛在報酬: **{potential_return:+.1f}%** (高潛力)")
                        elif potential_return > 10:
                            st.info(f"### 📈 潛在報酬: **{potential_return:+.1f}%** (中等潛力)")
                        elif potential_return > 0:
                            st.warning(f"### 📊 潛在報酬: **{potential_return:+.1f}%** (低潛力)")
                        else:
                            st.error(f"### 📉 潛在報酬: **{potential_return:+.1f}%** (可能高估)")
                        
                        # 關鍵數據
                        col_key1, col_key2, col_key3 = st.columns(3)
                        with col_key1:
                            st.metric("當前股價", f"${result['current_price']:.0f}")
                        with col_key2:
                            st.metric("內在價值", f"${result['intrinsic_value_per_share']:.0f}")
                        with col_key3:
                            st.metric("安全邊際", f"{potential_return:+.1f}%")
                        
                        # 詳細資訊
                        with st.expander("📊 詳細估值數據"):
                            col_detail1, col_detail2 = st.columns(2)
                            with col_detail1:
                                st.write("**財務數據**")
                                st.write(f"- 自由現金流: {result['current_fcf']:.1f} 億元")
                                st.write(f"- 流通股數: {result['shares_outstanding']:.1f} 億股")
                                st.write(f"- 當前市值: {result['current_market_value']:.1f} 億元")
                            
                            with col_detail2:
                                st.write("**估值結果**")
                                st.write(f"- 企業價值: {result['enterprise_value']:.1f} 億元")
                                st.write(f"- 5年現金流現值: {result['total_pv']:.1f} 億元")
                                st.write(f"- 終值現值: {result['terminal_pv']:.1f} 億元")
                        
                        # 現金流預測
                        st.subheader("📅 現金流預測")
                        df = pd.DataFrame(result['fcf_projections'])
                        st.dataframe(df, use_container_width=True, hide_index=True)

                        # 敏感度分析
                        st.markdown("---")
                        st.subheader("🎯 估值敏感度分析")
                        st.info("💡 此矩陣顯示在不同 **折現率** 與 **永續成長率** 假設下，該股票的潛在報酬率變化。")
                        
                        sensitivity_df = calculate_sensitivity_analysis(stock_data, growth_rate, terminal_growth, discount_rate)
                        
                        # 使用樣式凸顯正報酬
                        def highlight_returns(val):
                            if isinstance(val, str): return ''
                            color = '#d4edda' if val > 20 else '#fff3cd' if val > 0 else '#f8d7da'
                            text_color = '#155724' if val > 20 else '#856404' if val > 0 else '#721c24'
                            return f'background-color: {color}; color: {text_color}'

                        st.dataframe(
                            sensitivity_df.style.format("{:+.1f}%", na_rep="N/A").map(highlight_returns),
                            use_container_width=True
                        )
                        st.caption(f"基準參數: 成長率 {growth_rate}% | 永續成長 {terminal_growth}% | 折現率 {discount_rate}%")

            else:
                st.warning("⚠️ 請輸入股票代碼")

with tab2:
    st.markdown("### 🏆 潛在報酬排行榜")
    st.info("""
    **不設門檻，直接找出報酬最高的股票！**  
    系統會計算所有股票的 DCF 內在價值，並按**潛在報酬率**由高到低排序。  
    即使整體市場偏貴，您也能快速找到「相對最便宜」的投資標的。
    """)
    
    # 資料來源選擇
    use_db = False
    if STOCK_DB_AVAILABLE:
        use_db = st.toggle("🚀 使用本地資料庫 (快速掃描)", value=True, help="使用預先計算好的資料庫，速度極快，但資料可能不是最新的")
        
        if use_db:
            db = StockDatabase()
            last_update = "未知"
            try:
                # Check last update time of a random record
                df_check = db.get_all_stocks()
                if not df_check.empty and 'last_updated' in df_check.columns:
                    last_update = df_check['last_updated'].max()
            except:
                pass
            st.caption(f"📅 資料庫最後更新: {last_update}")
            
            if st.button("🔄 更新資料庫 (後台執行)", help="啟動後台腳本更新資料庫，可能需要一段時間"):
                import subprocess
                script_path = project_root / "scripts" / "update_stock_db.py"
                log_path = project_root / "update_db.log"
                
                if script_path.exists():
                    # Use shell redirection for robustness
                    cmd = f'"{sys.executable}" "{script_path}" > "{log_path}" 2>&1'
                    try:
                        subprocess.Popen(cmd, shell=True)
                        st.success("✅ 已啟動更新程序，請稍後再回來查看")
                        st.info(f"📝 詳細日誌將寫入: {log_path.name}")
                    except Exception as e:
                        st.error(f"❌ 啟動失敗: {e}")
                else:
                    st.error(f"❌ 找不到更新腳本: {script_path}")

            # Log Viewer
            log_path = project_root / "update_db.log"
            if log_path.exists():
                with st.expander("📝 查看更新日誌"):
                    if st.button("🔄 刷新日誌"):
                        pass
                    try:
                        with open(log_path, "r", encoding="utf-8") as f:
                            log_content = f.read()
                            # Show last 3000 chars
                            display_content = log_content[-3000:] if len(log_content) > 3000 else log_content
                            st.code(display_content, language="text")
                            
                            if "CRITICAL: FinMind API Limit Reached" in log_content:
                                st.error("⛔ 檢測到 API 限制錯誤 (402)。請求次數已達上限，請稍後再試。")
                            elif "Update Complete" in log_content:
                                st.success("✅ 更新已完成！")
                    except Exception as e:
                        st.error(f"無法讀取日誌: {e}")

    # 排行榜參數設定
    col_s1, col_s2 = st.columns(2)
    
    with col_s1:
        st.subheader("🎯 排行榜設定")
        
        # 顯示前幾名
        top_n = st.selectbox(
            "顯示排名前幾名",
            options=[3, 5, 10, 15, 20, 30, 50, 100],
            index=2,  # 預設顯示前 10 名
            help="選擇要顯示的股票數量，系統會從高到低排序"
        )
        
        # 類股篩選
        sector_filter = st.selectbox("類股篩選", [
            "全部", "半導體", "金融", "電子", "電信", "塑膠", "鋼鐵", "汽車",
            "水泥", "食品", "航運", "生技", "觀光", "建材營造"
        ])
        
        # 最小市值門檻（避免流動性太差的股票）
        min_market_cap = st.number_input(
            "最小市值門檻 (億元)", 
            value=50,
            step=25, 
            help="過濾掉市值太小、流動性差的股票"
        )
    
    with col_s2:
        st.subheader("📊 DCF參數")
        
        if use_db:
            st.info("💡 使用資料庫模式時，將顯示預先計算的結果 (基於行業預設參數)")
            st.warning("⚠️ 此模式下無法即時調整 DCF 參數，如需客製化參數請關閉「使用本地資料庫」")
        else:
            # 根據選擇的行業自動調整預設參數
            if INDUSTRY_PARAMS_AVAILABLE and sector_filter != "全部":
                industry_params = get_industry_params(sector_filter)
                default_growth = industry_params['growth_rate']
                default_terminal = industry_params['terminal_growth'] 
                default_discount = industry_params['discount_rate']
                
                st.success(f"✅ 已根據 **{sector_filter}** 行業特性自動調整參數")
            else:
                default_growth = 5.0
                default_terminal = 2.0
                default_discount = 8.0
            
            screen_growth = st.number_input("統一成長率 (%)", value=default_growth, step=0.1, key="screen_growth")
            screen_terminal = st.number_input("統一永續成長率 (%)", value=default_terminal, step=0.1, key="screen_terminal")
            screen_discount = st.number_input("統一折現率 (%)", value=default_discount, step=0.1, key="screen_discount")
    
    if st.button("🏆 開始分析排行榜", type="primary", use_container_width=True):
        if use_db and STOCK_DB_AVAILABLE:
            # Database Mode
            with st.spinner(f"🔍 正在從資料庫查詢 {sector_filter if sector_filter != '全部' else '所有'} 股票..."):
                db = StockDatabase()
                try:
                    # Get stocks
                    if sector_filter == "全部":
                        df_results = db.get_top_potential_stocks(limit=top_n * 2, min_market_cap=min_market_cap) # Get more to filter
                    else:
                        df_sector = db.get_stocks_by_sector(sector_filter)
                        # Filter by market cap and sort
                        df_results = df_sector[df_sector['market_cap'] >= min_market_cap].sort_values('potential_return', ascending=False).head(top_n)
                    
                    if not df_results.empty:
                        # Format columns for display
                        display_df = df_results.copy()
                        display_df = display_df.head(top_n)
                        
                        # Rename columns to match UI
                        display_df = display_df.rename(columns={
                            'code': '股票代碼',
                            'name': '公司名稱',
                            'sector': '類股',
                            'price': '當前股價',
                            'intrinsic_value': '內在價值',
                            'potential_return': '潛在報酬',
                            'market_cap': '市值(億)',
                            'fcf': '自由現金流(億)',
                            'data_source': '資料來源'
                        })
                        
                        # Format values
                        display_df['當前股價'] = display_df['當前股價'].apply(lambda x: f"${x:.0f}")
                        display_df['內在價值'] = display_df['內在價值'].apply(lambda x: f"${x:.0f}")
                        display_df['潛在報酬'] = display_df['潛在報酬'].apply(lambda x: f"{x:+.1f}%")
                        display_df['市值(億)'] = display_df['市值(億)'].apply(lambda x: f"{x:.0f}")
                        display_df['自由現金流(億)'] = display_df['自由現金流(億)'].apply(lambda x: f"{x:.1f}")
                        display_df['資料'] = display_df['資料來源'].apply(lambda x: "🔄" if x == 'auto_fetcher' else "🔧")
                        
                        # Add ranking
                        display_df.insert(0, '排名', [f"🏆 {i+1}" if i < 3 else f"#{i+1}" for i in range(len(display_df))])
                        
                        # Select columns to display
                        cols_to_show = ['排名', '股票代碼', '公司名稱', '類股', '當前股價', '內在價值', '潛在報酬', '市值(億)', '自由現金流(億)', '資料']
                        st.dataframe(display_df[cols_to_show], use_container_width=True, hide_index=True)
                        
                        st.success(f"✅ 從資料庫中找到 **{len(display_df)}** 檔符合條件的股票")
                    else:
                        st.warning("⚠️ 資料庫中沒有符合條件的股票，請嘗試更新資料庫或放寬篩選條件")
                        
                except Exception as e:
                    st.error(f"❌ 查詢資料庫失敗: {e}")
        else:
            # Live Fetch Mode (Original Logic)
            with st.spinner(f"🔍 正在分析 {sector_filter if sector_filter != '全部' else '所有'} 股票的潛在報酬..."):
                # 獲取所有股票數據
                all_stocks_data = get_all_stocks_for_screening()
            all_results = []
            failed_count = 0
            
            st.info(f"📊 分析條件: 最小市值 ≥ {min_market_cap:.0f}億, DCF參數: {screen_growth:.1f}%/{screen_terminal:.1f}%/{screen_discount:.1f}%")
            
            # 計算所有股票的DCF，不設報酬門檻
            for stock_data in all_stocks_data:
                try:
                    # 篩選類股
                    if sector_filter != "全部" and stock_data["sector"] != sector_filter:
                        continue
                    
                    # 計算DCF
                    result, error = calculate_dcf_with_potential_return(stock_data, screen_growth, screen_terminal, screen_discount)
                    
                    if result and not error:
                        # 只篩選市值（不篩選報酬率）
                        if result['current_market_value'] < min_market_cap:
                            continue
                        
                        data_source_icon = "🔄" if stock_data.get('data_source') == 'auto_fetcher' else "🔧"
                        all_results.append({
                            '排名': 0,  # 稍後填入
                            '股票代碼': stock_data.get('stock_code', 'N/A'),
                            '公司名稱': result['company_name'],
                            '類股': result['sector'],
                            '當前股價': f"${result['current_price']:.0f}",
                            '內在價值': f"${result['intrinsic_value_per_share']:.0f}",
                            '潛在報酬': f"{result['potential_return']:+.1f}%",
                            '市值(億)': f"{result['current_market_value']:.0f}",
                            '自由現金流(億)': f"{result['current_fcf']:.1f}",
                            '資料': data_source_icon,
                            '_潛在報酬數值': result['potential_return']  # 用於排序
                        })
                    else:
                        failed_count += 1
                except Exception as e:
                    failed_count += 1
                    continue
            
            # 按潛在報酬率排序（由高到低）
            if all_results:
                all_results.sort(key=lambda x: x['_潛在報酬數值'], reverse=True)
                
                # 只取前 N 名
                top_results = all_results[:top_n]
                
                # 填入排名
                for idx, result in enumerate(top_results, 1):
                    result['排名'] = f"🏆 {idx}" if idx <= 3 else f"#{idx}"
                    del result['_潛在報酬數值']  # 移除排序用的欄位
                
                # 顯示結果
                total_analyzed = len(all_results)
                st.success(f"✅ 共分析 **{total_analyzed}** 檔股票，顯示排名前 **{top_n}** 名")
                
                # 統計摘要
                avg_return = sum([r['_潛在報酬數值'] if '_潛在報酬數值' in r else float(r['潛在報酬'].replace('%', '').replace('+', '')) for r in all_results]) / len(all_results)
                top_avg_return = sum([float(r['潛在報酬'].replace('%', '').replace('+', '')) for r in top_results]) / len(top_results)
                
                col_stat1, col_stat2, col_stat3 = st.columns(3)
                with col_stat1:
                    st.metric("總分析數量", f"{total_analyzed} 檔")
                with col_stat2:
                    st.metric("市場平均報酬", f"{avg_return:+.1f}%")
                with col_stat3:
                    st.metric(f"前{top_n}名平均", f"{top_avg_return:+.1f}%")
                
                # 提示訊息
                # 獲取第一名的報酬率（注意：此時 '_潛在報酬數值' 已被刪除，需從字串解析）
                best_return = float(top_results[0]['潛在報酬'].replace('%', '').replace('+', '')) if top_results else -999
                
                if avg_return < 0:
                    st.warning(f"⚠️ 市場平均報酬為 **{avg_return:.1f}%**，整體估值偏高，建議謹慎投資")
                    
                    # 優先檢查是否有表現優異的個股
                    if best_return > 20:
                        st.success(f"✨ 發現亮點！雖然整體市場偏貴，但 **{top_results[0]['公司名稱']}** 潛在報酬達 **{best_return:+.1f}%**，值得關注！")
                    elif best_return > 0:
                        st.info(f"💡 雖然整體市場偏貴，但仍有少數股票如 **{top_results[0]['公司名稱']}** 出現正報酬機會。")
                    elif top_avg_return < -20:
                        st.error("❌ 即使是前幾名，平均報酬仍低於 -20%，建議等待更好的進場時機")
                    elif top_avg_return < 0:
                        st.info("💡 前幾名報酬仍為負值，但相對市場已是「最不貴」的選擇")
                    else:
                        st.success("✨ 前幾名出現正報酬！可能是市場中的價值窪地")
                else:
                    st.success("✨ 市場整體出現正報酬機會，是不錯的投資時機！")
                
                # 資料來源統計
                auto_count = sum(1 for r in top_results if r['資料'] == '🔄')
                fallback_count = len(top_results) - auto_count
                
                if auto_count > 0:
                    st.info(f"📡 真實資料: {auto_count} 檔 | 🔧 示範資料: {fallback_count} 檔")
                else:
                    st.warning("⚠️ 全部使用示範資料，建議檢查 AutoDataFetcher 模組狀態")
                
                # 顯示排行榜表格
                df_results = pd.DataFrame(top_results)
                st.dataframe(df_results, use_container_width=True, hide_index=True)
                
                # 失敗統計
                if failed_count > 0:
                    st.info(f"ℹ️ {failed_count} 檔股票因資料不足或計算錯誤而略過")
                    
            else:
                st.error("😞 沒有找到符合條件的股票")
                st.info("💡 **建議**: 降低最小市值門檻，或檢查資料來源是否正常")

# 說明區域
st.markdown("---")
with st.expander("ℹ️ DCF估值方法說明"):
    st.markdown("""
    **統一的DCF估值算法**
    
    🎯 **核心指標 - 潛在報酬率**:
    - 潛在報酬率 = (內在價值 - 當前股價) / 當前股價 × 100%
    - 正值表示股票被低估，負值表示可能高估
    
    📊 **DCF計算步驟**:
    1. **預測現金流**: 基於成長率預測未來5年現金流
    2. **計算終值**: 使用永續成長模型計算第5年後的價值
    3. **折現計算**: 用折現率將未來價值折現為現值
    4. **每股價值**: 企業價值除以流通股數
    
    🎨 **使用建議**:
    - **個股分析**: 深入了解單一股票的投資價值
    - **類股篩選**: 批量比較，找出最具潛力的投資標的
    - **參數調整**: 根據市場環境和個人判斷調整成長率和折現率
    
    ⚠️ **風險提醒**:
    - DCF估值對參數敏感，建議進行敏感度分析
    - 結合其他估值方法和基本面分析
    - 考慮總體經濟和產業趨勢
    """)

# 快速導航
st.markdown("---")
st.subheader("🔗 相關功能")

nav_col1, nav_col2, nav_col3 = st.columns(3)
with nav_col1:
    if st.button("📈 技術分析", use_container_width=True):
        st.switch_page("pages/📈_技術分析.py")
        
with nav_col2:
    if st.button("💼 投資組合", use_container_width=True):
        st.switch_page("pages/💼_投資組合管理.py")
        
with nav_col3:
    if st.button("🏠 返回主頁", use_container_width=True):
        st.switch_page("🏠_儀表板.py")
