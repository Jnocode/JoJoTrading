"""
WACC (加權平均資本成本) 計算器頁面
支援自動抓取股票數據或手動輸入
"""

import streamlit as st
import sys
from pathlib import Path

# 添加項目路徑
current_dir = Path(__file__).parent
project_root = current_dir.parent
src_path = project_root / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

# 嘗試導入 Stage 4 整合組件
try:
    from jojo_trading.ui.components.stage4_integration import Stage4IntegrationPanel
    STAGE4_AVAILABLE = True
except ImportError as e:
    STAGE4_AVAILABLE = False
    st.error(f"❌ Stage4IntegrationPanel 導入失敗: {e}")

# 頁面標題
st.title("⚙️ WACC 計算器")
st.markdown("**加權平均資本成本 (Weighted Average Cost of Capital) 計算工具**")

st.markdown("""
### 📚 關於 WACC

WACC 是公司籌資的平均成本，反映了公司整體資本結構的成本。它是 DCF 估值中的關鍵參數。

**計算公式**:
```
WACC = (E/V) × Re + (D/V) × Rd × (1-Tc)
```

其中:
- **E** = 權益市值 (Market Value of Equity)
- **D** = 債務總額 (Total Debt)
- **V** = E + D (企業總價值)
- **Re** = 權益成本 (Cost of Equity)，使用 CAPM 模型計算
- **Rd** = 債務成本 (Cost of Debt)
- **Tc** = 企業稅率 (Corporate Tax Rate)

**CAPM 公式** (計算權益成本):
```
Re = Rf + β × (Rm - Rf)
```

其中:
- **Rf** = 無風險利率 (Risk-free Rate)
- **β** = 貝塔係數 (Beta)
- **Rm** = 市場預期報酬率 (Market Return)
""")

st.markdown("---")

if STAGE4_AVAILABLE:
    # 初始化 Stage 4 面板
    if 'stage4_panel' not in st.session_state:
        st.session_state.stage4_panel = Stage4IntegrationPanel()
    
    # 渲染 WACC 計算面板
    st.markdown("### 💼 WACC 計算")
    
    # 創建 tabs 來組織內容
    tab1, tab2 = st.tabs(["🚀 計算 WACC", "📖 使用說明"])
    
    with tab1:
        st.info("💡 選擇計算模式: **自動抓取**股票數據或**手動輸入**財務數據")
        wacc_result = st.session_state.stage4_panel._render_wacc_panel()
        
        if wacc_result:
            st.success("✅ WACC 計算完成!")
            st.markdown("---")
            st.markdown("### 📊 如何使用 WACC")
            st.markdown("""
            WACC 可用於:
            1. **DCF 估值**: 作為折現率計算企業內在價值
            2. **投資決策**: WACC 是投資項目的最低報酬率門檻
            3. **績效評估**: 實際報酬率應高於 WACC
            4. **資本結構優化**: 找出最優的債務/權益比例
            
            **一般參考值**:
            - **低風險公司** (如公用事業): WACC 約 4-6%
            - **中等風險公司** (如製造業): WACC 約 6-10%
            - **高風險公司** (如科技業): WACC 約 10-15%
            """)
    
    with tab2:
        st.markdown("""
        ### 🎯 自動抓取模式
        
        1. **輸入股票代碼** (如: 2330)
        2. **調整 CAPM 參數**:
           - **Beta (β)**: 股票相對市場的波動性
             * β < 1: 低於市場波動 (防禦型)
             * β = 1: 等於市場波動
             * β > 1: 高於市場波動 (進攻型)
           - **無風險利率**: 通常使用 10 年期政府公債殖利率 (~1-2%)
           - **市場預期報酬率**: 歷史股市平均報酬率 (~8-10%)
           - **企業稅率**: 台灣營利事業所得稅率 (20%)
        
        3. **點擊「自動抓取並計算」**: 系統會:
           - 從 FinMind API 抓取財務數據
           - 自動計算市值 (股價 × 流通股數)
           - 抓取總債務和利息費用
           - 計算完整的 WACC
        
        ### ✋ 手動輸入模式
        
        適用於:
        - 私人公司 (沒有公開交易股票)
        - 假設情境分析
        - API 無法抓取數據時
        
        需要輸入:
        - 權益市值 (億元)
        - 總債務 (億元)
        - 利息費用 (億元)
        - CAPM 相關參數
        
        ### 💡 實用技巧
        
        **如何估算 Beta**:
        - 查詢財經網站 (Yahoo Finance, CMoney)
        - 使用產業平均 Beta
        - 保守估計: 使用 1.0 (市場平均)
        
        **無風險利率選擇**:
        - 台灣: 使用 10 年期公債殖利率 (~1.5%)
        - 美國: 使用 10 年期美國公債 (~4-5%)
        
        **市場報酬率**:
        - 台股歷史平均: 約 8-10%
        - 可查詢台灣加權指數長期年化報酬率
        
        **債務成本估算**:
        - 如果無利息費用數據: 使用 2.5-4% (台灣一般企業)
        - 高風險公司: 4-6%
        - 投資級公司: 2-3%
        """)
else:
    st.error("❌ Stage4IntegrationPanel 模組無法載入")
    st.markdown("""
    ### 故障排除
    
    請確認:
    1. `src/jojo_trading/ui/components/stage4_integration.py` 檔案存在
    2. `src/jojo_trading/analysis/wacc_calculator.py` 檔案存在
    3. Python 路徑設定正確
    4. 相關依賴已安裝
    
    如果問題持續,請聯繫技術支援。
    """)

# 側邊欄資訊
with st.sidebar:
    st.markdown("### 📌 快速連結")
    st.markdown("""
    - [回到首頁](/)
    - [DCF 估值分析](/📊_DCF分析)
    - [投資組合管理](/💼_投資組合管理)
    """)
    
    st.markdown("---")
    st.markdown("### 📚 相關資源")
    st.markdown("""
    - [WACC 計算詳解](https://www.investopedia.com/terms/w/wacc.asp)
    - [CAPM 模型介紹](https://www.investopedia.com/terms/c/capm.asp)
    - [Beta 係數說明](https://www.investopedia.com/terms/b/beta.asp)
    """)
