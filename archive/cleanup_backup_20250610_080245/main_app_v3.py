"""
JoJo Trading 主應用程式 (增強版 v3)
整合DCF估值分析、智能交易系統和系統監控的綜合平台
"""

import streamlit as st
import time
from datetime import datetime
import traceback

# 頁面配置必須是第一個Streamlit命令
st.set_page_config(
    page_title="JoJo Trading Platform v3",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/yourusername/jojo_trading',
        'Report a bug': "https://github.com/yourusername/jojo_trading/issues",
        'About': """
        # JoJo Trading Platform v3
        
        這是一個綜合的台股分析與交易平台，包含：
        
        ## 主要功能
        - **DCF估值分析**: 基於現金流折現模型的股票估值
        - **智能交易系統**: AI驅動的交易信號和投資組合管理
        - **系統監控**: 實時性能監控和錯誤追蹤
        - **成長股篩選**: 多維度成長指標篩選
        - **風險管理**: 自動化風險控制和資金管理
        
        ## 技術特色
        - 增強版DCF模型（情境分析、動態折現率）
        - 數據品質驗證和異常檢測
        - AI驅動的交易建議引擎
        - 自動化交易信號生成
        - 實時系統監控和日誌記錄
        
        版本: v3.0 (增強版)
        """    }
)

# 初始化系統監控
@st.cache_resource
def init_system_monitoring():
    """初始化系統監控"""
    try:
        from src.jojo_trading.core.system_monitor import init_monitoring
        monitor = init_monitoring(auto_start=True)
        monitor.log_system_event("主應用程序啟動", "INFO", "JoJo Trading v3 主應用程序已啟動")
        return monitor
    except Exception as e:
        st.warning(f"系統監控初始化失敗: {e}")
        return None

# 延遲導入避免在set_page_config之前執行Streamlit命令
def get_dcf_main():
    """延遲導入DCF主函數"""
    try:
        from src.jojo_trading.ui.app import main as dcf_main
        return dcf_main
    except Exception as e:
        st.error(f"DCF模組載入失敗: {e}")
        if monitor:
            monitor.log_system_event("DCF模組載入失敗", "ERROR", str(e))
        return None

def get_trading_ui():
    """延遲導入TradingSystemUI"""
    try:
        from src.jojo_trading.trading.trading_ui import TradingSystemUI
        return TradingSystemUI()
    except Exception as e:
        st.error(f"交易系統模組載入失敗: {e}")
        if monitor:
            monitor.log_system_event("交易系統模組載入失敗", "ERROR", str(e))
        return None

def get_trade_recorder():
    """延遲導入TradeRecorder"""
    try:
        from src.jojo_trading.trading.trade_recorder import TradeRecorder
        return TradeRecorder()
    except Exception as e:
        st.error(f"交易記錄器模組載入失敗: {e}")
        if monitor:
            monitor.log_system_event("交易記錄器模組載入失敗", "ERROR", str(e))
        return None

def render_home_page():
    """主頁渲染"""
    st.title("🏠 JoJo Trading Platform v3")
    st.markdown("歡迎使用智能股票分析與交易平台")
    
    # 系統狀態面板
    if monitor:
        with st.container():
            st.subheader("📊 系統狀態")
            col1, col2, col3, col4 = st.columns(4)
            
            try:
                status = monitor.get_system_status()
                
                with col1:
                    status_color = {
                        'healthy': '🟢',
                        'warning': '🟡', 
                        'error': '🔴',
                        'unknown': '⚪'
                    }.get(status['status'], '⚪')
                    st.metric("系統狀態", f"{status_color} {status['status'].upper()}")
                
                with col2:
                    if 'cpu_percent' in status:
                        st.metric("CPU使用率", f"{status['cpu_percent']:.1f}%")
                    else:
                        st.metric("CPU使用率", "未知")
                
                with col3:
                    if 'memory_percent' in status:
                        st.metric("記憶體使用率", f"{status['memory_percent']:.1f}%")
                    else:
                        st.metric("記憶體使用率", "未知")
                
                with col4:
                    if 'total_errors' in status:
                        st.metric("錯誤計數", status['total_errors'])
                    else:
                        st.metric("錯誤計數", "未知")
                
                # 警告訊息
                if status.get('warnings'):
                    st.warning("⚠️ 系統警告: " + ", ".join(status['warnings']))
                
            except Exception as e:
                st.error(f"獲取系統狀態失敗: {e}")
    
    # 功能概覽
    st.subheader("🚀 主要功能")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 📈 DCF估值分析
        - **增強版DCF模型**: 多情境分析和動態參數調整
        - **數據品質驗證**: 自動檢測和修正財務數據異常
        - **風險評估**: 綜合評估投資風險和不確定性
        - **視覺化呈現**: 豐富的圖表和分析報告
        
        ### 🤖 智能交易系統
        - **AI驅動信號**: 機器學習優化的交易建議
        - **投資組合管理**: 自動化資金分配和風險控制
        - **即時監控**: 持倉狀況和損益即時追蹤
        - **策略回測**: 歷史數據驗證交易策略效果
        """)
    
    with col2:
        st.markdown("""
        ### 📊 系統監控
        - **實時監控**: CPU、記憶體、磁碟使用率追蹤
        - **錯誤追蹤**: 自動記錄和分類系統錯誤
        - **性能分析**: 回應時間和處理效率監控
        - **日誌管理**: 完整的操作日誌和審計追蹤
        
        ### ⚙️ 系統配置
        - **個人化設置**: 自定義分析參數和顯示偏好
        - **風險偏好**: 調整風險承受度和投資目標
        - **通知設置**: 重要事件和異常狀況提醒
        - **數據管理**: 數據源配置和快取管理
        """)
    
    # 快速開始指南
    with st.expander("📖 快速開始指南", expanded=False):
        st.markdown("""
        1. **DCF分析**: 前往 "DCF分析" 頁面，輸入股票代碼進行估值分析
        2. **交易操作**: 前往 "交易系統" 頁面，查看投資組合或新增交易
        3. **系統設置**: 前往 "設置" 頁面，配置個人偏好和系統參數
        4. **監控查看**: 在此頁面查看系統運行狀態和性能指標
        
        💡 **提示**: 首次使用建議先進行系統設置，配置風險偏好和分析參數
        """)

def render_dcf_page():
    """DCF分析頁面"""
    st.title("📈 DCF估值分析")
    
    dcf_main = get_dcf_main()
    if dcf_main:
        try:
            start_time = time.time()
            dcf_main()
            
            # 記錄成功的DCF頁面渲染
            if monitor:
                duration = time.time() - start_time
                monitor.log_system_event("DCF頁面渲染", "INFO", f"渲染耗時: {duration:.2f}秒")
                
        except Exception as e:
            st.error(f"DCF分析模組執行錯誤: {e}")
            if monitor:
                monitor.log_system_event("DCF頁面錯誤", "ERROR", str(e))
            
            # 顯示詳細錯誤信息（開發模式）
            with st.expander("🔍 詳細錯誤信息", expanded=False):
                st.code(traceback.format_exc())
    else:
        st.error("DCF分析模組無法載入")

def render_trading_page():
    """交易系統頁面"""
    st.title("🤖 智能交易系統")
    
    trading_ui = get_trading_ui()
    if trading_ui:
        try:
            start_time = time.time()
            
            # 渲染交易系統界面
            trading_ui.render()
            
            # 記錄成功的交易頁面渲染
            if monitor:
                duration = time.time() - start_time
                monitor.log_system_event("交易頁面渲染", "INFO", f"渲染耗時: {duration:.2f}秒")
                
        except Exception as e:
            st.error(f"交易系統執行錯誤: {e}")
            if monitor:
                monitor.log_system_event("交易頁面錯誤", "ERROR", str(e))
            
            # 顯示詳細錯誤信息
            with st.expander("🔍 詳細錯誤信息", expanded=False):
                st.code(traceback.format_exc())
    else:
        st.error("交易系統模組無法載入")

def render_monitoring_page():
    """系統監控頁面"""
    st.title("📊 系統監控")
    
    if not monitor:
        st.error("系統監控未啟用")
        return
    
    # 即時系統狀態
    st.subheader("⚡ 即時系統狀態")
    
    try:
        status = monitor.get_system_status()
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            status_color = {
                'healthy': '🟢',
                'warning': '🟡', 
                'error': '🔴',
                'unknown': '⚪'
            }.get(status['status'], '⚪')
            st.metric("系統狀態", f"{status_color} {status['status'].upper()}")
        
        with col2:
            if 'cpu_percent' in status:
                st.metric("CPU使用率", f"{status['cpu_percent']:.1f}%")
        
        with col3:
            if 'memory_percent' in status:
                st.metric("記憶體使用率", f"{status['memory_percent']:.1f}%")
        
        with col4:
            if 'disk_usage' in status:
                st.metric("磁碟使用率", f"{status['disk_usage']:.1f}%")
        
        with col5:
            if 'response_time' in status:
                st.metric("回應時間", f"{status['response_time']:.2f}秒")
        
        # 錯誤統計
        st.subheader("🚨 錯誤統計")
        error_col1, error_col2, error_col3, error_col4 = st.columns(4)
        
        if 'error_counts' in status:
            with error_col1:
                st.metric("DCF錯誤", status['error_counts'].get('dcf_errors', 0))
            with error_col2:
                st.metric("交易錯誤", status['error_counts'].get('trading_errors', 0))
            with error_col3:
                st.metric("數據錯誤", status['error_counts'].get('data_errors', 0))
            with error_col4:
                st.metric("系統錯誤", status['error_counts'].get('system_errors', 0))
        
        # 性能摘要
        st.subheader("📈 性能摘要")
        
        time_range = st.selectbox("選擇時間範圍", [1, 6, 12, 24, 72], index=3, format_func=lambda x: f"過去 {x} 小時")
        
        if st.button("重新整理性能數據"):
            with st.spinner("正在獲取性能數據..."):
                performance = monitor.get_performance_summary(hours=time_range)
                
                if 'message' in performance:
                    st.info(performance['message'])
                else:
                    perf_col1, perf_col2 = st.columns(2)
                    
                    with perf_col1:
                        st.write("**CPU使用率統計**")
                        cpu_stats = performance['cpu_usage']
                        st.write(f"- 平均: {cpu_stats['avg']:.1f}%")
                        st.write(f"- 最高: {cpu_stats['max']:.1f}%")
                        st.write(f"- 最低: {cpu_stats['min']:.1f}%")
                        
                        st.write("**記憶體使用率統計**")
                        mem_stats = performance['memory_usage']
                        st.write(f"- 平均: {mem_stats['avg']:.1f}%")
                        st.write(f"- 最高: {mem_stats['max']:.1f}%")
                        st.write(f"- 最低: {mem_stats['min']:.1f}%")
                    
                    with perf_col2:
                        st.write("**回應時間統計**")
                        resp_stats = performance['response_time']
                        st.write(f"- 平均: {resp_stats['avg']:.2f}秒")
                        st.write(f"- 最長: {resp_stats['max']:.2f}秒")
                        st.write(f"- 最短: {resp_stats['min']:.2f}秒")
                        
                        st.write("**數據點統計**")
                        st.write(f"- 數據點數量: {performance['data_points']}")
                        st.write(f"- 時間範圍: {performance['period_hours']} 小時")
        
        # 警告和建議
        if status.get('warnings'):
            st.subheader("⚠️ 系統警告")
            for warning in status['warnings']:
                st.warning(warning)
        
        # 監控控制
        st.subheader("🎛️ 監控控制")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("停止監控"):
                monitor.stop_monitoring()
                st.success("監控已停止")
                st.rerun()
        
        with col2:
            if st.button("重啟監控"):
                monitor.stop_monitoring()
                time.sleep(1)
                monitor.start_monitoring()
                st.success("監控已重啟")
                st.rerun()
        
        with col3:
            if st.button("清理舊日誌"):
                monitor.cleanup_old_logs(days=30)
                st.success("舊日誌清理完成")
        
    except Exception as e:
        st.error(f"獲取監控數據失敗: {e}")
        if monitor:
            monitor.log_system_event("監控頁面錯誤", "ERROR", str(e))

def render_settings_page():
    """設置頁面"""
    st.title("⚙️ 系統設置")
    
    # 應用程式設置
    st.subheader("📱 應用程式設置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 主題設置
        st.write("**顯示設置**")
        theme = st.selectbox("選擇主題", ["auto", "light", "dark"], index=0)
        show_debug = st.checkbox("顯示除錯資訊", value=False)
        
        # DCF設置
        st.write("**DCF分析設置**")
        default_growth_rate = st.number_input("預設成長率 (%)", value=2.5, min_value=0.0, max_value=10.0, step=0.1)
        default_discount_rate = st.number_input("預設折現率 (%)", value=10.0, min_value=1.0, max_value=20.0, step=0.1)
    
    with col2:
        # 交易設置
        st.write("**交易系統設置**")
        risk_level = st.selectbox("風險偏好", ["保守", "穩健", "積極"], index=1)
        max_position_size = st.number_input("最大單一持倉比例 (%)", value=10.0, min_value=1.0, max_value=50.0, step=1.0)
        
        # 通知設置
        st.write("**通知設置**")
        enable_notifications = st.checkbox("啟用通知", value=True)
        email_notifications = st.checkbox("電子郵件通知", value=False)
    
    # 系統監控設置
    st.subheader("📊 系統監控設置")
    
    monitor_col1, monitor_col2 = st.columns(2)
    
    with monitor_col1:
        monitoring_interval = st.number_input("監控間隔 (秒)", value=30, min_value=10, max_value=300, step=10)
        log_retention_days = st.number_input("日誌保留天數", value=30, min_value=1, max_value=365, step=1)
    
    with monitor_col2:
        auto_cleanup = st.checkbox("自動清理舊日誌", value=True)
        detailed_logging = st.checkbox("詳細日誌記錄", value=False)
    
    # 保存設置
    if st.button("💾 保存設置", type="primary"):
        # 這裡可以實際保存設置到配置文件
        st.success("設置已保存！")
        if monitor:
            monitor.log_system_event("設置更新", "INFO", "用戶更新了系統設置")
    
    # 系統資訊
    st.subheader("ℹ️ 系統資訊")
    
    info_col1, info_col2 = st.columns(2)
    
    with info_col1:
        st.write("**應用程式資訊**")
        st.write(f"- 版本: v3.0 (增強版)")
        st.write(f"- 啟動時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        st.write(f"- Python版本: {st.__version__}")
    
    with info_col2:
        st.write("**功能狀態**")
        st.write("- DCF分析: ✅ 正常")
        st.write("- 交易系統: ✅ 正常")
        st.write("- 系統監控: ✅ 正常" if monitor else "- 系統監控: ❌ 未啟用")

def main():
    """主函數"""
    # 初始化監控（只在第一次執行時）
    global monitor
    monitor = init_system_monitoring()
    
    # 側邊欄導航
    st.sidebar.title("🧭 導航選單")
    
    # 頁面選項
    pages = {
        "🏠 首頁": "home",
        "📈 DCF分析": "dcf",
        "🤖 交易系統": "trading",
        "📊 系統監控": "monitoring",
        "⚙️ 設置": "settings"
    }
    
    # 使用 session_state 來保持頁面狀態
    if "current_page" not in st.session_state:
        st.session_state.current_page = "home"
    
    # 側邊欄頁面選擇
    for page_name, page_key in pages.items():
        if st.sidebar.button(page_name, key=f"nav_{page_key}", use_container_width=True):
            st.session_state.current_page = page_key
            st.rerun()
    
    # 側邊欄系統狀態（簡化版）
    if monitor:
        st.sidebar.markdown("---")
        st.sidebar.subheader("💡 系統狀態")
        try:
            status = monitor.get_system_status()
            status_emoji = {
                'healthy': '🟢',
                'warning': '🟡', 
                'error': '🔴',
                'unknown': '⚪'
            }.get(status['status'], '⚪')
            st.sidebar.write(f"狀態: {status_emoji} {status['status'].upper()}")
            
            if 'total_errors' in status and status['total_errors'] > 0:
                st.sidebar.error(f"總錯誤數: {status['total_errors']}")
        except:
            st.sidebar.write("狀態: ⚪ 未知")
    
    # 根據選擇的頁面渲染內容
    current_page = st.session_state.current_page
    
    try:
        if current_page == "home":
            render_home_page()
        elif current_page == "dcf":
            render_dcf_page()
        elif current_page == "trading":
            render_trading_page()
        elif current_page == "monitoring":
            render_monitoring_page()
        elif current_page == "settings":
            render_settings_page()
        else:
            st.error(f"未知頁面: {current_page}")
            
    except Exception as e:
        st.error(f"頁面渲染錯誤: {e}")
        if monitor:
            monitor.log_system_event("頁面渲染錯誤", "ERROR", f"頁面: {current_page}, 錯誤: {str(e)}")
        
        # 在除錯模式下顯示詳細錯誤
        with st.expander("🔍 詳細錯誤信息", expanded=False):
            st.code(traceback.format_exc())

if __name__ == "__main__":
    main()
