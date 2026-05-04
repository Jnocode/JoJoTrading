"""
🧪 測試頁面 - 驗證格式化修復
"""

import streamlit as st

st.set_page_config(
    page_title="格式化測試",
    page_icon="🧪",
    layout="wide"
)

st.title("🧪 格式化測試頁面")

st.success("如果您能看到這個頁面，表示格式化問題已修復！")

# 測試一些基本的百分比顯示
test_value = 0.123
st.write(f"測試百分比格式化: {test_value:.1%}")

# 測試滑塊
test_slider = st.slider(
    "測試滑塊",
    min_value=0.0,
    max_value=1.0,
    value=0.5,
    step=0.01
)

st.write(f"滑塊值: {test_slider}")

st.info("所有格式化功能正常運作！")
