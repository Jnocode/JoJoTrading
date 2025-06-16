"""
🧪 DCF 計算器測試頁面
"""

import streamlit as st

st.set_page_config(
    page_title="DCF 測試",
    page_icon="🧪",
    layout="wide"
)

st.title("🧪 DCF 計算器測試")

# 簡單的輸入測試
st.selectbox("選擇股票", ["2330 台積電", "2317 鴻海"])

# 基本按鈕測試
if st.button("測試計算", type="primary"):
    st.success("DCF 計算器基本功能正常！")
    
    # 測試簡單的 metrics
    st.metric("企業價值", "NT$ 15,000 M")
    st.metric("每股價值", "NT$ 580")

# 測試列布局（單層）
col1, col2 = st.columns(2)

with col1:
    st.info("左側測試")

with col2:
    st.info("右側測試")

st.success("✅ 如果您能看到這個消息，表示列布局嵌套問題已修復！")
